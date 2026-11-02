# Literature Workspace

Store search logs, paper notes, and `references.bib` here. A benchmark task is
not considered validated until related work and novelty gates are recorded.

Current records:

- `search_20261027.md`: targeted related-work and novelty audit.
- `arxiv_verified_20261027.json`: arXiv metadata snapshot for the verified IDs.
- `references.bib`: generated metadata-only BibTeX; full texts still need audit.
- `search_20261101.md`: second pass, aimed at the three structural gaps named in
  `../GROWTH-PLAN-20261101.md`. Records the source failures (arXiv returned 429
  or timed out on every query, so this pass has **zero arXiv results**;
  Semantic Scholar mostly 429; CORE needs an API key; IACR ePrint and IOS
  OneSearch failed) and the eight gap groups the candidates answer.
- `candidates_20261101.json`: 59 metadata-only candidates from that pass, with
  zero arXiv-ID overlap against `arxiv_verified_20261027.json`. Authors are
  `null` where the index did not return them; nothing is inferred.

Both 2026-11-01 files are metadata only. No full text has been read, so any
number quoted from them is the abstract's own claim, not a verified result.
