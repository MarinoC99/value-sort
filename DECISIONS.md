# Decisions

Judgment calls not specified in SPEC.md or the build instructions. One line of rationale each.

| # | Step | Decision | Rationale |
|---|---|---|---|
| 1 | 1 | Package named `value_sort`, built with hatchling. | Matches the product name in SPEC.md; hatchling is uv's default backend. |
| 2 | 1 | Only `pytest` declared; no runtime deps yet. | Working agreement: every new dependency is approved before it is added. |
| 3 | 1 | Unimplemented `make` targets exit 1 instead of no-op. | A target that silently succeeds could be mistaken for one that produced output. |
| 4 | 1 | Python pinned to 3.11 via uv-managed interpreter (`.python-version`). | System Python is 3.9; the spec calls for 3.11. |
