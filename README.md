# Value Sort

> **Status: scaffold only. No results yet.** The full README (problem, finding,
> limitations, setup) comes in Step 10.

A re-ranker that reorders Amazon search results by rating credibility, per-unit price,
and what reviewers say a product is good at. The contract is [SPEC.md](SPEC.md);
judgment calls are logged in [DECISIONS.md](DECISIONS.md).

## What the data shows

Across 331,095 priced items in Health & Household, the simple mean rating is
4.25 while the count-weighted mean is 4.48. Items with more ratings rate
higher. Three explanations are consistent with this data and it cannot
distinguish between them: popular products may genuinely be better;
better-rated products may accumulate more ratings through higher sales; or
sellers with more volume may solicit reviews more aggressively. The gap
matters for the ranker because it determines which direction low-count items
get shrunk toward — the choice of C is not neutral.

## Setup

```bash
uv sync
make test
```

*Data: Amazon Reviews 2023, McAuley Lab, UC San Diego. Independent student project, not
affiliated with or endorsed by Amazon.*
