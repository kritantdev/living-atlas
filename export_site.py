# Copyright (C) 2026 Kritant Bhatia
# SPDX-License-Identifier: AGPL-3.0-only
"""
Living Atlas -- D8B3: export_site.py

Writes the static data files the launched page reads, using serving_api.py's OWN
loading and shaping code, so the files cannot drift from what the API serves.

    data/nodes.json     == GET /nodes
    data/clusters.json  == GET /clusters
    data/edges.json     == GET /edges?include_unverified=true, allowlisted fields only
                           (no author names, no hand-written notes -- see EDGE_ALLOWED_FIELDS)

Nothing else is exported (no /meta, rankings or similarity: the page never requests them).

Usage (PowerShell, from the project folder, venv active):
    python export_site.py                      # export to ./data
    python export_site.py --compare-api        # also compare each file to the live API
                                               # (start the API in another window first)
    python export_site.py --out data --api http://127.0.0.1:8000

Safety checks (the export FAILS and writes nothing if any trips):
    - forbidden keys anywhere in the data (authors, abstract, api keys, ...)
    - local paths or key-looking strings in any string value

STALE-ON-NEW-DATA: the falsifiability notes and edge verification judgments are
hand-maintained tables inside serving_api.py. They are baked into this export.
Re-read them whenever the underlying data is regenerated.
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

try:
    from fastapi.encoders import jsonable_encoder  # type: ignore  # same encoder FastAPI uses for responses
    import serving_api as api  # type: ignore  # private pipeline module, not published in this repository
except ImportError as e:
    sys.exit("export_site.py needs fastapi and the private pipeline module serving_api.py, "
             f"which are not part of this repository ({e}).")

FORBIDDEN_KEYS = {
    "authors", "author", "author_names", "abstract", "abstracts", "summary_text",
    "api_key", "apikey", "key", "token", "secret", "password",
}
# Values that must not appear in the public export.
FORBIDDEN_VALUE_PATTERNS = [
    re.compile(r"[A-Za-z]:\\"),                 # Windows path (D:\LivingAtlas...)
    re.compile(r"\\\\Users\\\\|/Users/|/home/"),  # user home paths
    re.compile(r"(?i)api[_-]?key"),
    re.compile(r"(?i)\bsk-[A-Za-z0-9]{10,}"),
    re.compile(r"(?i)MISTRAL_API_KEY|GROQ_API_KEY|GEMINI_API_KEY"),
]


def walk(obj, path=""):
    """Yield (path, key, value) for every dict key and (path, None, value) for list items."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}.{k}", k, v
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield f"{path}[{i}]", None, v
            yield from walk(v, f"{path}[{i}]")


def content_check(name, obj):
    problems = []
    for p, k, v in walk(obj):
        if k is not None and str(k).lower() in FORBIDDEN_KEYS:
            problems.append(f"{name}: forbidden key at {p}")
        if isinstance(v, str):
            for pat in FORBIDDEN_VALUE_PATTERNS:
                if pat.search(v):
                    problems.append(f"{name}: suspicious string at {p}: {v[:80]!r}")
                    break
    return problems


# Edges are exported through an ALLOWLIST. The API's edge objects carry `bridges`
# (real author names and paper ids) and a hand-written `verification_note` that names
# individuals; neither belongs in a public file, and the page reads only
# verification_status. Any field added to edges later is excluded until listed here.
EDGE_ALLOWED_FIELDS = [
    "domain_a", "domain_b", "jaccard", "overlap_coefficient",
    "shared_author_count", "raw_shared_author_count", "verification_status",
]


def sanitize_edges(edges):
    return [{k: e[k] for k in EDGE_ALLOWED_FIELDS if k in e} for e in edges]


def fetch_live(base, endpoint):
    with urllib.request.urlopen(base + endpoint, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--compare-api", action="store_true")
    ap.add_argument("--api", default="http://127.0.0.1:8000")
    args = ap.parse_args()

    api.load_all()  # fills api._data exactly as the server does at startup

    exports = {
        "nodes.json": ("/nodes", api._data["nodes"]),
        # get_edges(include_unverified=True) returns the full list; the page requests that form
        "clusters.json": ("/clusters", api._data["clusters"]),
        "edges.json": ("/edges?include_unverified=true", api._data["edges"]),
    }

    # Encode exactly as FastAPI would, then round-trip through JSON so what we
    # check and write is what the page will parse.
    prepared = {}
    for fname, (_, raw) in exports.items():
        enc = jsonable_encoder(raw)
        if fname == "edges.json":
            enc = sanitize_edges(enc)
        prepared[fname] = json.loads(json.dumps(enc, ensure_ascii=False))

    problems = []
    for fname, obj in prepared.items():
        problems += content_check(fname, obj)
    if problems:
        print("EXPORT REFUSED -- content check failed:")
        for p in problems[:40]:
            print("  ", p)
        if len(problems) > 40:
            print(f"   ... and {len(problems) - 40} more")
        sys.exit(1)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for fname, obj in prepared.items():
        (out / fname).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {len(prepared)} files to {out.resolve()}")
    for fname, obj in prepared.items():
        size = (out / fname).stat().st_size
        n = len(obj) if isinstance(obj, (list, dict)) else "-"
        print(f"  {fname:14s} {size/1024:8.1f} KB   items={n}")

    if args.compare_api:
        print("\nComparing each file to the live API (parsed JSON equality):")
        ok_all = True
        for fname, (endpoint, _) in exports.items():
            live = fetch_live(args.api, endpoint)
            if fname == "edges.json":
                live = sanitize_edges(live)  # the only intended difference from the API
            written = json.loads((out / fname).read_text(encoding="utf-8"))
            same = live == written
            ok_all &= same
            print(f"  {fname:14s} {endpoint:34s} {'IDENTICAL' if same else 'DIFFERS'}")
            if not same:
                print("     live type/len:", type(live).__name__, len(live),
                      "| file type/len:", type(written).__name__, len(written))
        if not ok_all:
            print("\nAt least one file differs from the API. Stop and find out why "
                  "before touching the page.")
            sys.exit(2)
        print("\nAll files match the API.")


if __name__ == "__main__":
    main()
    