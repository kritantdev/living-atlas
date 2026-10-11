# Copyright (C) 2026 Kritant Bhatia
# SPDX-License-Identifier: AGPL-3.0-only
"""Updates the PULL line inside the page directly, from papers.db. Run after every new pull:
    python update_pull.py
Optional:  python update_pull.py --db papers.db --page index.html
"""
import argparse
import re
import sqlite3
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--db", default="papers.db")
ap.add_argument("--page", default="index.html")
args = ap.parse_args()

n, first, last = sqlite3.connect(args.db).execute(
    "SELECT COUNT(*), MIN(published), MAX(published) FROM papers WHERE published IS NOT NULL AND published != ''").fetchone()
if not n:
    sys.exit(f"No dated papers found in {args.db}; page not changed.")

with open(args.page, encoding="utf-8", newline="") as f:      # newline="" keeps the file's own line endings
    html = f.read()
pattern = re.compile(r'const PULL = \{[^}\n]*\};')
if len(pattern.findall(html)) != 1:
    sys.exit(f"Expected exactly one 'const PULL = {{...}};' line in {args.page}; page not changed.")

old = pattern.search(html).group(0)
new = f'const PULL = {{ papers: {n}, from: "{first[:10]}", to: "{last[:10]}" }};'
if old == new:
    print(f"{args.page} is already up to date:\n  {new}")
else:
    with open(args.page, "w", encoding="utf-8", newline="") as f:
        f.write(html.replace(old, new))
    print(f"Updated {args.page}\n  was: {old}\n  now: {new}")
