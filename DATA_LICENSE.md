# Data licence

The files in `data/` (`nodes.json`, `clusters.json`, `edges.json`) are released under the
**Creative Commons Attribution-ShareAlike 4.0 International licence (CC BY-SA 4.0)**.
The full legal text is in [`data/LICENSE`](data/LICENSE); a plain-language summary is at
https://creativecommons.org/licenses/by-sa/4.0/.

You may share and adapt the data, including commercially, as long as you:

1. **give credit**, link to the licence, and say whether you made changes; and
2. **share your adapted version under the same licence** (CC BY-SA 4.0 or a compatible one).

**Suggested credit:**

> Living Atlas, by Kritant Bhatia (2026). Data licensed under CC BY-SA 4.0.
> https://github.com/kritantdev/living-atlas

## What the data is

Labels, topic names, domain names and notes about a snapshot of arXiv cs.LG papers. Topic labels and
names were written by language models; the notes on under-explored candidates were checked by hand
against the papers' abstracts. Provided as-is, without warranty.

## Models that wrote the labels

- Mistral AI Ministral models, via the Mistral API: problem labels, topic audits, candidate ratings.
- Google Gemini 3.1 Flash-Lite, via the Gemini API: domain names and descriptions.
- Meta Llama 3.1 8B Instruct, via Groq: some early problem labels.

If you use these labels to train or fine-tune a model, check the licence and terms of the providers above; the Llama 3.1 Community License in particular has rules about naming models trained on its outputs. Meta, Llama, Mistral, Google and Gemini are trademarks of their owners; this project is independent and not endorsed by them.

## What this licence does not cover

- The papers themselves. They belong to their authors; arXiv IDs are given so you can find them.
- The code in this repository, which is under AGPL-3.0-only (see `LICENSE`).
- Any terms attached by the model providers above. This licence cannot override them.
