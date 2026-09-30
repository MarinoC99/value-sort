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
