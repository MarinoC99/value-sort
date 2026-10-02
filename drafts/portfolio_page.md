# Value Sort: re-ranking marketplace search results for the shopper

*Independent student project using the public Amazon Reviews 2023 dataset (McAuley Lab,
UC San Diego). Not affiliated with or endorsed by Amazon.*

**Status: partial results.** Stage 1 is built. Stage 2's pack-size extractor is built and
audited; the unit-price score and the ranker that combines the signals are not built yet.
No experiment has been run, and nothing here claims a lift in sales or satisfaction.

Three findings, stated up front. The unit-price extractor measures 93.1%
precision against a 90% guardrail set before labelling, on an interval
(85.8-96.8%) that straddles the threshold. The module reaches roughly 19%
of the category, which is far narrower than the spec assumed when it
weighted unit price as an equal partner to the rating signal. And the
working agreement written to stop the coding agent fabricating results
caught overclaiming in the human-written summaries as well as in the
model's output, consistently in the direction of claiming more (documented in
CONSIDERATIONS.md section 10). An earlier draft gave a ratio; the underlying count
drifted three times and was dropped.

---

## How it was built

A written working agreement governed an AI coding agent: never fabricate a number; stop and
ask before large downloads, new dependencies or paid API calls; one step at a time, each
committed with its reasoning; every judgment call logged. SPEC.md was amended in place, with
superseded claims kept visible.

The agreement was aimed at the model, but in practice it caught
overclaiming in the human-written summaries more often, always in the
same direction: text asserting more than the repository supported.

## The problem

A marketplace's default sort is tuned to its own goals (sales, ad revenue, fulfillment
cost), which overlap with a shopper's but aren't the same. It leaves three gaps open:

1. **Star ratings are shown without their sample size.** A hypothetical 4.9 stars from 46
   ratings is displayed with the same authority as 4.5 from 8,431. (That pair is
   illustrative, from the spec; every other figure on this page comes from the repository.)
2. **Listed prices aren't comparable prices.** Pack sizes vary across near-identical items,
   so the cheaper-looking listing can be the more expensive one per unit.
3. **What decides a purchase is buried in review text.** Taste, mixability, tolerance: no
   filter, no sort.

Value Sort re-orders a result set on those three axes, in stages ordered by how likely each
one is to be confidently wrong: arithmetic first, text parsing second, LLM extraction last
and only if it passes a pre-set grounding test.

## The data

One category, Health & Household: **797,563 items**. Only **41.5%** have a price, so
ranking works on the **331,095 priced items**. The metadata was checked row by row against a
strict schema before any modeling: 0 malformed rows, 40 items dropped for having no title,
and every missing price counted by reason rather than silently discarded.

## What was built

### 1. Credibility-Adjusted Rating (CAR)

A Bayesian average that pulls ratings backed by only a few reviews toward a reference mean,
and leaves heavily reviewed items almost untouched. The reference mean and prior weight are
computed over each result set, so a protein powder is compared with protein powders, not
the department average. A stored fallback (mean 4.2486, weight 50, from the 331,095 priced
items) is used only when a result set has fewer than 30 rated items, and that result is
flagged.

What the computation shows across the priced pool:

- **CAR separates items the star display shows as tied.** Stars take only 41 distinct
  values; CAR takes 35,520 (one per distinct rating-and-count pair), or 256 when shown to
  two decimals. Star ratings in the data are rounded to one decimal, so the recorded
  quality signal has 41 possible values across 331,095 items. CAR therefore discriminates
  between items the rating field presents as identical.
- **The prior weight decides the ranking.** Against a plain star-rating sort, CAR's top 20
  (using the simple mean) shares 15 of 20 items at weight 25, 5 at weight 50, and none at
  weights of 120 or more.
  The default weight (the median rating count) is a convention, not a principled choice, and
  needs a defence before the ranker ships.
- **The reference mean isn't neutral.** The simple mean rating is 4.25; weighted by number
  of ratings it is 4.48, because items with more ratings rate higher. The data can't say
  why, but the choice sets which way low-count items are pulled.

These describe what CAR does, not whether it helps a shopper. That needs an experiment
(see below).

### 2. Unit-price extraction

A rule-based extractor reads pack count and size from the title and a fixed set of product
fields. It returns a size only when its sources agree, or when one clear source is
uncontradicted. Otherwise it abstains and the item keeps its listed price. A wrong unit
price is worse than none.

**The audit came first.** 200 items were drawn at random from the priced pool and committed
before any extractor code existed. The extractor was developed on separate samples, and the
confidence threshold and scoring rules were fixed before the labels arrived. The labels
were written by hand.

## The measured result

**Precision: 93.1% (81 of 87 extractions correct), 95% confidence interval 85.8–96.8%.**

That clears the ≥90% guardrail set before labelling. But the interval straddles the
threshold, so the defensible claim is that the point estimate passes, not that true
precision exceeds 90%. The interval width follows from the audit's size and was known
before labelling.

Four errors (excluding three length-sold items the label format couldn't express), in two
classes. Three share one shape: a number that describes the product rather than what the
price buys. A transfer bench's 400 lb load capacity, a wheelchair's own 30 lb weight, and
the 35-count canister a cover is sized to fit. The fourth is a container-capacity case the
labelling guide didn't cover.

This is the only measured quality number in the project.

## The coverage finding

Unit pricing reaches far less of the category than the original spec assumed:

| | |
|---|---|
| Items with a price | 41.5% of the category |
| Priced items that get a pack size | 151,922 of 331,095 (45.9%), about 19% of all items |
| Audit items that are durable goods, where unit price isn't meaningful | 65 of 200 |
| Audit items with an expressible size that get one | 83 of 113 (the other 30 abstain) |

The module is correct 93% of the time when it returns a size, silent on more than half of
items, and inapplicable in principle to roughly a third of priced items. (The durable-goods
share of unpriced items is unmeasured.) That makes unit price a targeted correction on
consumables, not a general reordering. The spec originally weighted it as an equal partner
to the rating signal; it has been amended to say so.

## What isn't built

This list is long and specific on purpose. A reader should be able to tell
exactly where the project stops.

- **The unit-price score and the combined ranker.** The extractor exists; turning pack sizes
  into a per-unit price and blending the signals doesn't yet.
- **Result sets.** CAR's per-set reference values need a matcher that builds realistic result
  sets. Until it exists, CAR has only been run across the whole priced pool.
- **Review-attribute extraction (Stage 3).** Not started. It ships only if at least 95% of
  extracted attributes trace to the review sentences cited for them. If not, it's cut and
  the cut is reported.
- **Offline evaluation and the demo page.**
- **Any experiment.** There's no traffic and no clickstream, so there is no conversion,
  revenue or satisfaction result, simulated or otherwise. The spec defines the experiment
  that would be needed: user-level randomization, three arms, a quality-adjusted purchase
  rate as the primary metric, and kill criteria written in advance.

---

*Repository: SPEC.md (the contract and its amendments), DECISIONS.md (every judgment call),
CONSIDERATIONS.md (the reasoning), reports/ (every figure above).*
