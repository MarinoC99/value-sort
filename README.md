# Value Sort

> **Status: scaffold only. No results yet.** The full README (problem, finding,
> limitations, setup) comes in Step 10.

A re-ranker that reorders Amazon search results by rating credibility, per-unit price,
and what reviewers say a product is good at. The contract is [SPEC.md](SPEC.md);
judgment calls are logged in [DECISIONS.md](DECISIONS.md).

## Setup

```bash
uv sync
make test
```

*Data: Amazon Reviews 2023, McAuley Lab, UC San Diego. Independent student project, not
affiliated with or endorsed by Amazon.*
