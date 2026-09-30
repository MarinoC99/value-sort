# Value Sort — product spec v0.1

> **Status: partial results.** Stage 1 is built. Stage 2's pack-size extractor is built and
> audited; the NUP score and composite ranker are not yet built (Step 7). The unit-price
> extractor's precision is measured at 93.1% (95% CI 85.8-96.8%, n=87) against 200
> hand-labelled items. Stage 3 (attribute extraction) is not built and remains conditional on
> its grounding guardrail. No experiment has been run: there is no traffic, no clickstream,
> and no simulated lift anywhere in this project.
>
> *Superseded status banner (v0.1, kept for the record):* ~~**Status: intended work. No
> results produced yet.** Nothing has been built, run, or measured. Every number below is a
> formula, a pre-committed threshold, or an assumption.~~

## Amendments

Both amendments are already implemented. Each original claim is kept in place below and
marked as superseded.

| # | Summary | Section |
|---|---|---|
| 1 | Priors C and m are computed over the candidate set at rank time, not over the category. | [§3 CAR, Amendment 1](#amendment-1) |
| 2 | NUP is a targeted correction on consumables, not a signal with reach comparable to CAR. | [§3 Composite, Amendment 2](#amendment-2) |

A re-ranker that reorders an already-retrieved set of Amazon search results on three axes
the default sort ignores: how credible a rating is, what a product costs per unit, and what
reviewers say it is good at.

---

## 1. Problem

Three failure modes, all visible on page one of a crowded consumable category:

1. **Ratings are shown without their sample size.** 4.9 stars from 46 ratings outranks 4.5
   from 8,431. The first carries far less information but is displayed with identical
   authority and sorted with identical weight.
2. **Listed prices are not comparable prices.** Pack size and serving size vary across
   near-identical items. A $34.99 tub and a $61.99 tub can be $1.75 and $0.84 per serving.
   Unit-price display is inconsistently populated and placed.
3. **The deciding dimensions are locked in prose.** Mixability, aftertaste, tolerance —
   these drive satisfaction and returns, and exist only in review text. No facet, no filter,
   no sort.

### Root cause

Not an oversight. A marketplace's default ordering is tuned against the marketplace's
objective: GMV, ad revenue, fulfillment economics, near-term conversion. Those correlate
with shopper value but are not identical to it. Where they diverge, the interface resolves
in favor of the marketplace. The product opportunity is that gap.

---

## 2. Scope

**In scope.** Re-ordering an already-retrieved result set. Candidate set taken as given.
Every position must be explainable in one sentence a shopper would understand.

**Not in scope.** Retrieval or query understanding. Review-fraud detection. Personalization
(v1 ranks identically for everyone, so any effect is attributable to the ranking logic).
Shipping cost — destination-, cart-, and membership-dependent, resolves only at checkout;
modeled as a toggleable input, never a fetched fact.

### Staging — two modules committed, one conditional

| Stage | Module | Failure mode | Status |
|---|---|---|---|
| 1 | Credibility-Adjusted Rating | None available. Arithmetic over two numeric fields already in the data. | Committed |
| 2 | Normalized Unit Price | Mis-parsed pack sizes. Wrong, but countable against a hand-labeled set. Low-confidence items fail open. | Committed |
| 3 | Attribute Match Score | Fabricated attributes. An LLM can assert support the text does not contain. | Conditional |

Stage 3 ships only if it clears the attribute-grounding guardrail. If not, it is cut, the cut
is reported, and stages 1–2 stand as the finished system. **There is no half-built state:**
after stage 1 there is a working re-ranker; after stage 2, one with a measured accuracy
number behind it.

### Data reality

Amazon Reviews 2023 (McAuley Lab, UCSD) — 571M reviews, 48M items. Metadata carries
`average_rating`, `rating_number`, `price`, `categories`, `details`. September 2023 snapshot.
**No sales volume, no shipping cost, no live pricing.** Every claim is bounded by this.

---

## 3. Metrics

### North star

**Qualified Purchase Rate (QPR).** Share of product-search sessions ending in a purchase that
is not returned within the return window and not followed by a repeat search for the same
need within 14 days. Deliberately harder to move than conversion.

### Input metrics

**Credibility-Adjusted Rating (CAR)** — committed

```
CAR = (v / (v + m)) · R  +  (m / (v + m)) · C

R = item average_rating
v = item rating_number
C = category mean rating                                   ← superseded, see Amendment 1
m = prior weight (default: category median rating count)   ← superseded, see Amendment 1
```

<a id="amendment-1"></a>
> **Amendment 1: priors are candidate-set-local, not category-level.** Supersedes the
> definitions of C ("category mean rating") and m ("category median rating count") above.
>
> C and m are computed over the candidate set at rank time. Health & Household spans
> vitamins, toilet paper, thermometers, router batteries and protein powder, so a prior
> fitted across all 797,563 items is the wrong reference class - an item should shrink
> toward the mean of comparable products, not the department average. Where a candidate set
> holds fewer than 30 rated items, a stored fallback is used (C = 4.2486 simple, m = 50,
> computed over the 331,095 priced items) and the item is flagged. Observed per-query priors
> ranged C 4.28-4.52 and m 54-123, confirming the variation the amendment assumed. Note that
> those figures came from a prototype matcher since removed, so they are indicative and are
> re-verified at Step 7.

Few ratings pull toward the category average; thousands leave the item untouched. `m` is the
most consequential parameter in the system and must be reported with sensitivity analysis
across at least three values.

**Normalized Unit Price (NUP)** — committed

```
NUP = price / (count × size_per_unit)
rank input = −z(ln NUP)
```

Log scale, because $0.10 means something different at $0.80 than at $8.00. Items whose pack
size cannot be extracted confidently **fail open**: they keep their listed price and are
flagged in the UI rather than penalized. Silently mis-parsing is worse than not parsing.

**Attribute Match Score (AMS)** — conditional

```
AMS = Σ w_a · sentiment(a, item) · relevance(a, query)
      over attributes a in the category schema
```

Attributes extracted from review text by an LLM into a fixed per-category schema. Extraction
runs offline, cached per item. Every extracted attribute must carry a pointer back to the
review sentences that produced it, so a score can be audited rather than trusted.

*Known limitation:* in v1 the schema is author-chosen, so dimensions are imposed rather than
induced from the corpus. This buys stability — a fixed schema is what makes the grounding
guardrail enforceable and keeps weights meaningful across runs — at the cost of being a
positioning grid rather than a discovered one. Inducing and curating candidate dimensions is
the v2 question, not opened until stage 3 clears its guardrail.

### Composite

```
ValueScore = w₁·z(CAR) + w₂·(−z(ln NUP)) + w₃·z(AMS)
defaults: w₁ = 0.45, w₂ = 0.35, w₃ = 0.20
```

*Superseded framing:* listing NUP at 0.35 beside CAR at 0.45 implied the two signals have
comparable reach. See Amendment 2.

<a id="amendment-2"></a>
> **Amendment 2: NUP is a targeted correction, not a co-equal signal.** Supersedes the
> framing above.
>
> Unit-price ranking reaches a minority of the category. 41.5% of items carry a price; of 200
> hand-labelled audit items, 65 are durable goods where unit price is not meaningful at any
> level of data quality; and of the 113 with a size expressible in the format, the extractor
> returns one for 83 (three further items had a determinable size the format could not
> express). NUP is therefore a targeted correction on consumables rather than a general
> reordering. The weight is unchanged for now, because it applies only to items where a unit
> price exists, but the spec no longer claims the two signals have comparable reach.

If stage 3 is cut, `w₃` goes to zero and the rest renormalize to 0.56 / 0.44. Removing the
conditional module is a configuration change, not a rewrite.

Weights are a product decision, not a learned parameter, and that is intentional for v1.
Fixed interpretable weights mean every position can be explained to a shopper and audited by
a reviewer. Learning them is a v2 question, opened only after the interpretable version has a
measured baseline.

### Guardrails

| Metric | Definition | Threshold |
|---|---|---|
| Revenue per session | GMV ÷ search sessions | No loss greater than 3% |
| Impression concentration | Gini of impressions across candidate set | Must not rise vs. control |
| Ranking latency | p95 added latency | Under 40 ms |
| Unit-price precision | Correct pack-size extractions, 200-item hand-labeled audit | ≥ 90% |
| Attribute grounding | Extracted attributes traceable to cited review text | ≥ 95% |

### Deliberately not optimized

- **Click-through rate.** A better sort should need fewer clicks. Rising CTR is as consistent
  with confusion as with interest. Diagnostic only.
- **Time on page.** Same problem, opposite sign.
- **Raw conversion rate.** Moves with discounting and demand; counts returned purchases as wins.

---

## 4. Experiment plan

| | |
|---|---|
| Randomization | User, not session. Reordering between visits is worse than either arm and would contaminate the 14-day repeat-search component of QPR. |
| Exposure | Users searching the pilot category. Assigned at first qualifying search, sticky thereafter. |
| Arms | Control · CAR-only · Full Value Sort. The middle arm attributes the effect; a win from the full model alone says nothing about which idea earned it. |
| Primary | QPR. Powered for 2% relative lift, 80% power, α = 0.05, two-sided. |
| Duration | Three full weeks minimum. Two complete weekly cycles plus a third to test novelty decay. No holiday overlap. |
| Pre-registered segments | New vs. returning · mobile vs. desktop · high vs. low basket · attribute-intent vs. generic queries. |
| Novelty check | Week 1 vs. week 3 within treatment. A decaying lift is an interface artifact, not a ranking improvement. |

---

## 5. Kill criteria

Written before the experiment runs, because criteria written afterward are rationalizations.

1. **Revenue per session falls >3%, CI excluding zero.** Kill outright. Recovering shopper
   value by destroying marketplace value does not ship.
2. **QPR lift CI includes zero at full sample.** One iteration permitted, weights only. If the
   second read is null, kill.
3. **Unit-price precision <90% on audit.** Kill the NUP module, ship the rest. A wrong per-unit
   price is a concrete harm, worse than the status quo it was meant to fix.
4. **Return rate flat and query-refinement rate up.** Kill. Shoppers working harder and
   choosing no better is the exact failure this set out to fix.
5. **p95 added latency >40 ms, not recoverable by pre-computation.** Kill.
6. **Attribute grounding <95%.** Kill the AMS module. An unauditable LLM-derived score inside a
   ranking system is a liability the feature has not earned.

**Double down if:** QPR lift concentrated in attribute-intent queries, return rate down,
revenue flat. That pattern means the re-ranker helps precisely where the default sort has
least information — and justifies opening learned weights, personalization, and expansion
beyond consumables.

---

## 6. Limitations

The experiment above cannot be run. No live traffic; the data is a 2023 snapshot with no
sales, no shipping, no clickstream. Presenting simulated results as evidence of lift would be
dishonest, so the build does not do it.

What it produces instead, offline and clearly bounded:

- **Rank displacement.** Kendall's tau between default and re-ranked orders; share of top-10
  positions changed. Describes how much the system does, not whether it helps.
- **Face validity audit.** Hand-labeled sample recording whether each large position change is
  defensible. Subjective, labeled as such.
- **Extraction precision.** The one genuinely measured number here, on a 200-item hand-labeled
  set.

A format limitation found during labelling: the truth format's unit list (oz, fl oz, lb, g,
kg, mg, ml, l, ct) cannot express length or gallon measures. Four audit items had a fully
determinable size the format could not hold - a 10 yd tape roll, a 1000 ft foil roll, a
286 yd ribbon set, and a 1 gallon soap. Three, labelled NONE, are reported as a separate
category rather than as extractor failures; the soap was converted to 128 fl oz and scored
normally. Whether unit price should support length at all is an open question.

**Honest summary:** this demonstrates that the re-ranking produces materially different and
plausibly better orderings, and specifies exactly what evidence would be needed to claim more.

---

*Data source: Amazon Reviews 2023, McAuley Lab, UC San Diego. Independent student project,
not affiliated with or endorsed by Amazon.*
