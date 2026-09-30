# Decisions

Judgment calls not specified in SPEC.md or the build instructions. One line of rationale each.

| # | Step | Decision | Rationale |
|---|---|---|---|
| 1 | 1 | Package named `value_sort`, built with hatchling. | Matches the product name in SPEC.md; hatchling is uv's default backend. |
| 2 | 1 | Only `pytest` declared; no runtime deps yet. | Working agreement: every new dependency is approved before it is added. |
| 3 | 1 | Unimplemented `make` targets exit 1 instead of no-op. | A target that silently succeeds could be mistaken for one that produced output. |
| 4 | 1 | Python pinned to 3.11 via uv-managed interpreter (`.python-version`). | System Python is 3.9; the spec calls for 3.11. |
| 5 | 2 | Metadata is streamed and only the six contract fields are written to `data/raw/meta_<Category>.slim.parquet`; the 2.47 GB JSONL is never stored. | User choice: disk footprint. The stream is sha256-verified against the published hash, so the slim file is provably from the source. |
| 6 | 2 | `categories` is not kept in the slim file. | User instruction: contract fields only. Anything needing it later (e.g. leaf-category candidate sets) requires a re-stream and a contract change. |
| 7 | 2 | `price`, `average_rating`, `rating_number`, `details` are stored as raw JSON text, not typed. | No silent coercion before Step 3; the loader owns typing and fails loudly. |
| 8 | 2 | C = unweighted mean of `average_rating`; m = median `rating_number`; both over items with rating_number >= 1. | Standard Bayesian-average prior; zero-rating items have no rating to average. Count-weighted C is reported for reference only. |
| 9 | 2 | Profile written to `reports/profile_<Category>.json` (committed). | Step 4 must read m and C from a versioned artifact, not a hardcoded value. |
| 10 | 6 | If Step 6 is reached, reviews are sampled by streaming the review JSONL and keeping only the top-N items' reviews; never downloaded in full. | User decision: the 11.4 GB review file is out of scope for this machine. |
| 11 | 2 | `PYTHONPATH=src` exported in the Makefile and `pythonpath = ["src"]` set for pytest. | uv flags the editable-install `.pth` as hidden on macOS and Python 3.11.16 ignores hidden `.pth` files; re-applied on every `uv run`, so it must be fixed in project config. |
| 12 | 4 | **SPEC amendment.** C and m are computed over the candidate set at rank time, not over the whole category. If a candidate set has < 30 items, fall back to global values and flag the result. | User decision: a protein powder should shrink toward comparable products, not the department average. Supersedes SPEC §3 "C = category mean rating" and Step 4's "m and C come from the Step 2 profile". |
| 13 | 7 | Candidate sets are built by title keyword match. No leaf categories, no re-stream. | User decision: with C/m per candidate set (#12), leaf categories aren't needed as a reference class. |
| 14 | 3 | Only items with a valid price > 0 enter ranking (`loader.priced`). | User decision: unpriced items don't appear in real results, and mixing them in makes z-scores inconsistent across rows. |
| 15 | 4 | The Step 4 sensitivity check varies C (simple mean, count-weighted mean, candidate-set mean) as well as m (25, 120, 500). | User decision. |
| 16 | 3 | Price rules: `—`, `from $X`, and ≤ 0 become null with a counted reason; outliers are kept unclipped; bad JSON or missing fields fail loudly. | User decision. Clipping would be a silent data edit; the log transform handles outliers. |
| 17 | 3 | Price strings that match none of the known patterns fail loudly; they are not nulled. | My call: an unforeseen format is exactly what should be surfaced, not quietly absorbed. None occur in this data. |
| 18 | 3 | Rows with empty or whitespace-only titles are dropped at load and counted (40 here). They aren't malformed and don't raise. | User decision: no title means the item can't be candidate-matched or pack-size parsed, so it can't take part in ranking. |
| 19 | 3 | The loader checks every row, then raises once with the full list of malformed rows (and also refuses if the fetch manifest recorded any bad JSON lines). | My call: one run shows every problem, not just the first; still no silent drops. |
| 20 | 3 | `Item` is pydantic strict + `extra="forbid"` + frozen. `average_rating` and `rating_number` are nullable. | My call: no type coercion, no fields outside the contract. Nullable because Step 4 must represent null/zero-rating edge cases, even though none occur in this data. |
