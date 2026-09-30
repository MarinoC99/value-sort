# Value Sort

> **Status: partial results.** Stage 1 is built. Stage 2's pack-size extractor is built and
> audited; the NUP score and composite ranker are not yet built (Step 7). The unit-price
> extractor's precision is measured at 93.1% (95% CI 85.8-96.8%, n=87) against 200
> hand-labelled items. Stage 3 (attribute extraction) is not built and remains conditional on
> its grounding guardrail. No experiment has been run: there is no traffic, no clickstream,
> and no simulated lift anywhere in this project.

The full README (problem, finding, limitations, setup) comes in Step 10.

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

## Rating resolution

Across 331,095 priced items the displayed star rating takes only 41 distinct values, while
CAR (m = 50, simple C) takes 35,520, one per distinct rating-and-count pair, or 256 when
shown to two decimals, so it separates items the star display shows as tied.

## Unit-price extraction: measured precision

The extractor's precision is 93.1% (81 of 87 extractions correct), which
clears the >=90% guardrail set in SPEC.md before any labels existed. The
95% confidence interval is 85.8-96.8%. With 87 extractions, that interval
straddles the threshold, so the defensible claim is that the point estimate
passes, not that true precision exceeds 90%. The interval width was known
before labelling began and is a consequence of the audit sample size, not
of the result.

The 200 audit labels were drawn at random from the priced pool and committed
before the extractor existed; the extractor was developed on non-overlapping
samples. Four errors were found (excluding the format-limited items), three of
them the same shape: a number describing the product itself rather than what
the price buys - load capacity (400 lbs), the item's own weight (30 lbs), and
the capacity of a different product the item fits (35-count canisters).

## What the module actually reaches

Unit-price ranking applies to a minority of the category, and the
constraints compound. 41.5% of Health & Household items carry a price.
Of the 200 hand-labelled audit items, 65 are durable goods - braces,
monitors, canes, brushes, devices - where unit price is not a meaningful
comparison at any level of data quality. Of the 113 items with a size
expressible in the format (three more had a size the format could not
express), the extractor returns one for 83; it abstains on the other 30
rather than guess.

The resulting characterisation of the module: correct 93% of the time when
it returns a size, silent on more than half of items, and inapplicable in
principle to roughly a third of priced items (the durable-goods share of
unpriced items is unmeasured). This makes Normalized Unit Price a targeted
correction on consumables rather than a general reordering, which is a
narrower claim than SPEC.md assumed when it weighted NUP as a co-equal
signal alongside CAR.

## Setup

```bash
uv sync
make test
```

*Data: Amazon Reviews 2023, McAuley Lab, UC San Diego. Independent student project, not
affiliated with or endorsed by Amazon.*
