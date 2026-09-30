# Value Sort — considerations and decisions

A record of what was decided, what was rejected, and why. Complements `SPEC.md` (what the
system is) and `DECISIONS.md` (what the build did). This file is the reasoning.

---

## 1. Data access: why there is no Amazon API in this project

**The official route is closed.** PA-API 5.0 was retired on 15 May 2026 and replaced by the
Creators API, which requires an Amazon Associates account with at least 10 qualifying sales
in the trailing 30 days. That is a chicken-and-egg gate for a research project: you need the
API to build the thing that would generate the sales that unlock the API.

**Even with access, the API does not carry what this project needs.**

| Needed | Available in Creators API? |
|---|---|
| Star rating, review count | No. The `CustomerReviews` resource was removed. |
| Shipping cost in dollars | No. Only booleans (`IsFreeShippingEligible`, `IsAmazonFulfilled`). |
| Unit sales | No. Sellers see their own via SP-API; nobody else sees any. |

**Rejected:** scraping amazon.com. Violates Conditions of Use, actively blocked, and
unpublishable.

**Chosen:** Amazon Reviews 2023 (McAuley Lab, UCSD). Free, citable, reproducible, and carries
`average_rating`, `rating_number`, `price` and `details` — the exact fields the official API
withholds. Cost: a September 2023 snapshot with no sales, shipping, or live pricing. Every
claim in the project is bounded by that, stated up front rather than discovered later.

---

## 2. Framing: from three analyses to one thesis

The original three ideas were separate analyses. They became one project by naming the
common cause: **a marketplace's default sort optimizes the marketplace's objective function,
not the shopper's.** GMV, ad revenue, fulfillment economics and near-term conversion
correlate with shopper value but are not identical to it. The product opportunity is the gap.

That reframing is what makes this a PM project rather than a data exercise, and it is the
answer to "what tradeoff did you make and why."

### How each original idea was translated

| Original | Became | Why |
|---|---|---|
| Rating/price matrix | Credibility-Adjusted Rating (CAR) | The interesting variable isn't price against rating, it's *how much the rating can be trusted*. Bayesian shrinkage by sample size makes that computable. |
| Price including shipping | Normalized Unit Price (NUP) | Shipping cost does not exist as a field anywhere, in any source. Unit-price confusion is the same consumer harm, is actually derivable from title and `details`, and is arguably the sharper finding. |
| Perceptual map | Attribute Match Score (AMS) | Kept the idea, made it LLM-driven rather than spec-driven, which is also where the project's AI-product story lives. |

---

## 3. Staging: sequenced by hallucination risk, not by interest

The three modules are not equally safe to build, so they do not ship as a bundle.

| Stage | Module | Failure mode | Status |
|---|---|---|---|
| 1 | CAR | None available — arithmetic over two numeric fields | Committed |
| 2 | NUP | Mis-parsed pack sizes. Wrong, but countable against a hand-labeled set. | Committed |
| 3 | AMS | Fabricated attributes. An LLM can assert support the text does not contain. | Conditional |

The consequence worth stating plainly: **the project has no half-built state.** After stage 1
there is a working re-ranker. After stage 2, one with a measured accuracy number behind it.
Stage 3 is additive, and if it fails its grounding guardrail it gets cut and the cut gets
reported. Cutting it is a finding, not a failure.

The composite was designed so removing stage 3 zeroes `w₃` and renormalizes the other two —
a configuration change, not a rewrite.

---

## 4. The latent-attribute gap (known, deferred)

The spec's AMS uses an **author-chosen** schema. The dimensions are imposed, not induced from
the corpus. A perceptual map in the classical sense derives its axes from the data.

**Why imposed, for v1:** a fixed schema is what makes the 95% grounding guardrail
enforceable and keeps the composite weights meaningful across runs. Rediscovered dimensions
shift the AMS component under the composite every run. Unsupervised methods on review text
also reliably surface "sentiment polarity" and "which product this is" as the first two
components — both true, both useless for positioning.

**The v2 shape:** induce candidate dimensions by embedding and clustering review sentences,
filter by variance across items (an attribute every product scores 4.5 on tells you nothing),
have an LLM label the clusters, then curate down to 5–8 by hand and freeze. That turns "where
did the axes come from" into "induced from the corpus, then curated against a discrimination
threshold — here are the rejects and why."

**Not opened until stage 3 clears its guardrail.** Noted so it can be named in an interview,
not built.

---

## 5. Honesty constraints

These are the rules that decide what the project is allowed to claim.

- **No simulated lift.** There is no traffic and no clickstream. Presenting simulated
  conversion or revenue results as evidence would be dishonest, so the build does not compute
  them. Step 8 of the build brief forbids it explicitly, because a coding agent left alone
  will produce that chart.
- **Demo data is labeled as fabricated.** The eight products on the spec page are invented.
  The formula running on them is real. The page says so in both places.
- **A status banner states what is and isn't built or measured.** It said no results existed
  until partial results did, and was then replaced. README.md and SPEC.md carry it verbatim,
  and a test fails if the two differ.
- **A missing value is data; a broken row is a bug.** Only the second stops the pipeline.
  Nulls get counted and reported by reason.
- **Fail open, never guess.** An item whose pack size can't be parsed keeps its listed price
  and is flagged. A silently wrong per-unit price is worse than the status quo it was meant
  to fix.
- **What the project can actually establish:** that the re-ranking produces materially
  different and plausibly better orderings, plus one genuinely measured number (extraction
  precision). Everything beyond that is specified as what *would* be needed.

---

## 6. Decisions made during the build

| # | Decision | Reasoning |
|---|---|---|
| 1 | Health_and_Household, streamed to a slim Parquet | Same 2.47 GB transfer either way, but writes only the six contract fields — 109 MB on disk instead of 2.5 GB. The schema contract already ruled out the discarded fields. |
| 2 | Reviews never downloaded whole | 11.4 GB. If stage 3 happens, stream and filter to top-N items only. If stage 3 is cut, never needed at all. |
| 3 | **Spec amendment:** C and m computed over the candidate set at rank time, not globally | Health_and_Household contains vitamins, toilet paper, thermometers and protein powder. A prior across 797,563 unrelated items is the wrong reference class. Shrink toward comparable products, not the department average. |
| 4 | Fallback priors used only below 30 candidates | C = 4.2486 (simple), m = 50, computed over priced items only. Stored in a file, read not hardcoded, labeled fallback-only. |
| 5 | No leaf categories, no re-stream | Decision 3 removes the need for them. Candidate sets get built by title keyword match in Step 7. |
| 6 | Filter to price > 0 rather than fail open on missing price | 58% of items have no price. An unpriced item wouldn't appear in a real search result, and leaving it in makes z-scores inconsistent across rows. 331,095 items survive. |
| 7 | Extreme prices kept, not clipped | The log transform handles them. Silent winsorizing is a data edit disguised as cleaning. |
| 8 | Empty titles dropped at load, before the price check | Can't be candidate-matched or pack-size parsed, so can't participate in ranking. Checking title first keeps the price-null counts interpretable. 40 rows. |
| 9 | Unexpected price text fails the load rather than becoming null | Agent's call. Known formats ("—", "from $X", $0, negative) become null and are counted; anything unrecognized is a bug, not data. |
| 10 | Sensitivity sweep spans the distribution, not the median | m = 25, 120, 500 sit near p50/p77/p90 of rating count across the whole category; m = 50, the priced-pool median, was added later (row 18). C varied two ways, simple and count-weighted; candidate-set C was deferred to Step 7 (row 12). |
| 11 | Weights are a product decision, not learned | Fixed interpretable weights mean every position can be explained to a shopper and audited. Learning them is v2, after the interpretable version has a baseline. |
| 12 | Candidate-set-mean C sensitivity deferred to Step 7; prototype matcher reverted | A throwaway keyword matcher in Step 4 would have produced sensitivity results from different matching logic than the final system uses. Step 4 varies C over simple and count-weighted means only. (DECISIONS #22) |
| 13 | Fallback priors computed over priced items, not the whole category | The whole-category values (C = 4.1266, m = 24) include 466k items that can never be ranked. The fallback file is role-tagged, and the reader refuses any file without the tag, so it can't become a default by accident. (DECISIONS #21) |
| 14 | Step 4 sweep run over the whole priced pool, compared pairwise | No candidate sets exist yet, and using the fallback priors as a "baseline" would have treated them as a default. (DECISIONS #23) |
| 15 | CAR edge cases: zero ratings = C exactly; null count = not computable, ranked last | v = 0 is defined by the formula. Imputing v = 0 for an unknown count would invent evidence. (DECISIONS #24) |
| 16 | Ties broken by more ratings, then ID | average_rating is rounded to 0.1 in the source (41 distinct values), so exact ties are common. (DECISIONS #25) |
| 17 | The < 30 floor counts rated items, not raw set size | Only rated items inform C and m. Identical in this data, where every priced item is rated. (DECISIONS #26) |
| 18 | m = 50 flagged as a convention needing justification | It's the priced-pool median, not a principled choice, and the sweep shows m decides the ranking: at m = 50 the top 20 sits mid-transition between m = 25 and m = 120. (DECISIONS #27) |
| 19 | Audit set: simple random 200 from the priced pool, fixed seed | Represents what the ranker actually sees. Stratifying would need a product-type classifier nobody has built. (DECISIONS #29) |
| 20 | Extractor and labeller see the same fields; labels come from the file, not Amazon | Disagreements then measure the extractor, not information asymmetry. Live listings may differ from the 2023 snapshot. (DECISIONS #30) |
| 21 | Scoring rules fixed before labelling | Correct = same dimension and total within 1%; NONE-with-extraction is wrong; coverage reported beside precision; N/A reported separately. Rules chosen after seeing labels would be rationalizations. (DECISIONS #31) |
| 22 | **Audit-first sequencing** | 200 labelling targets committed before any extractor code existed; extractor developed on non-overlapping samples; audit rows never inspected during development. Git order shows the sequence. (DECISIONS #32) |
| 23 | Extractor accepts a pack size only on agreement or one uncontradicted source | "Never guess" made operational: fixed confidence levels, and any disagreeing strong source means abstain. (DECISIONS #33) |
| 24 | Confidence threshold 0.7 set in config before labels | Picking it after seeing precision would be tuning on the audit set. (DECISIONS #34) |
| 25 | item_weight never a source; Number of Items only corroborates; Unit Count of 1 ignored | Development data showed shipping or placeholder weights, pack-vs-piece ambiguity, and filler values. (DECISIONS #35) |
| 26 | item_weight not used as a tie-breaker either (CitraSolv) | Where title (16 oz) and item_volume (2 gal dilution yield) disagreed, item_weight would have resolved it, but using it would reverse #25's exclusion for one audit item. Abstaining costs coverage, not precision. (DECISIONS #45) |
| 27 | Container capacity ignored; kits abstain; nutrition grams and mg dosages never sizes | "9 oz cup (360 ct)" and "25g protein" describe what the item holds or contains per dose, not what the price buys. (DECISIONS #36) |
| 28 | **"Pouch" gap left unfixed** | "Pouch" is capacity on some listings and a consumable package on others. A rule would break real cases, so the known miss is recorded instead. (DECISIONS #36) |
| 29 | "N pack" is a multiplier up to 24, a piece count above | "600 Pack" spoons vs "6 Pack" batteries. Judgment from development data, measured by the audit. (DECISIONS #37) |
| 30 | **No concentrate rule written from a single audit item** | One example (CitraSolv) isn't enough to write a rule, and a rule fitted to an audit item would inflate precision on the set it's scored against. (DECISIONS #46) |
| 31 | Guardrail judged on the point estimate; 95% Wilson interval always reported | About 87 extractions give roughly ±6 points. Hiding the interval would overstate what 200 labels can show. (DECISIONS #38) |
| 32 | Format-limited items reported beside the pre-registered rule, never instead of it | The split (95.3%) was requested after labelling; the pre-registered figure (93.1%) stays the headline. (DECISIONS #39) |

---

## 7. Observation worth keeping

Across 331,095 priced items, the simple mean rating is 4.25 and the count-weighted mean is
4.48. Items with more ratings rate higher. Three explanations fit and the data cannot
separate them: popular products may be better; better products may accumulate more ratings
through higher sales; or high-volume sellers may solicit reviews more aggressively.

It matters for the ranker because it sets which direction low-count items shrink toward. The
choice of C is not neutral.

---

## 8. Open items

- Stage 3 go/no-go depends on reading ~10 extractions by hand and checking whether the cited
  sentences actually support the scores.
- The NUP score (`price / (count × size)`, `−z(ln NUP)`) and the composite ranker are not
  built. Only the pack-size extractor and its audit exist. Step 7.
- Paper bowls (#132): labelled `50 x 12 oz`, extracted `50 ct`. The labelling guide never said
  how to label container capacity. Unsettled. (DECISIONS #41)
- Whether unit price should support length units (yd, ft) at all, or whether length-sold items
  should always fail open. Three audit items hit this. (DECISIONS #40)
- Guide/scorer unit mismatch: the guide lists `mg`, which the scorer rejects, and omits `gal`
  (and `qt`, `pt`), which the scorer accepts. No label used `mg`, so no score was affected.
  Recorded, not fixed. (DECISIONS #42)
- Per-query m values (54–123) straddle the phase change the Step 4 sweep found between
  m = 25 and m = 120, so CAR may be near-inert on some queries and decisive on others. Those
  values came from the reverted prototype matcher; re-verify at Step 7 with the real one.
  (DECISIONS #28)

---

## 9. Results so far

The extractor's precision is 93.1% (81 of 87 extractions correct), which clears the >=90%
guardrail set in SPEC.md before any labels existed. The 95% confidence interval is
85.8-96.8%. With 87 extractions, that interval straddles the threshold, so the defensible
claim is that the point estimate passes, not that true precision exceeds 90%.

Two error classes. Three of the four errors are a number describing the product itself
rather than what the price buys: load capacity (400 lbs), the item's own weight (30 lbs), and
the capacity of a different product the item fits (35-count canisters). The fourth is the
paper-bowls container-capacity labelling gap (DECISIONS #41).

| Coverage | Figure |
|---|---|
| Items with a price | 41.5% of the category |
| Priced items that get a pack size (whole pool) | 151,922 of 331,095 (45.9%) |
| Audit items that get a pack size | 87 of 200 (43.5%) |
| Audit items that are durable goods (unit price not meaningful) | 65 of 200 |
| Audit items with a size expressible in the format that the extractor returns | 83 of 113 (30 abstained) |
| Audit items with a determinable size the format can't express | 3 |

**This contradicts what SPEC.md originally assumed about NUP's reach.** The spec weighted NUP
at 0.35 beside CAR at 0.45, as a co-equal signal. Measured, it reaches a minority of the
category and is a targeted correction on consumables. SPEC.md now carries this as
Amendment 2.

---

## 10. What the verification discipline actually caught

The working agreement was written to stop the coding agent fabricating results. In practice it caught overclaiming from the humans more often, by roughly five instances to two.

The agent's first instance was its own Step 4 test, which assumed SPEC.md's 4.9-vs-4.5 example would flip order at m = 50. It doesn't. The agent checked the spec, found no such claim, and rewrote the test to verify what the formula actually does rather than adjusting numbers until it passed.

The agent's second instance was the p50/p80/p95 framing of the m sweep in its Step 2 summary. m = 500 sits near p90 of rating count, not p95. The framing was carried into row 10 of this file and repeated unchecked by the human reviewers for several turns, and by the agent itself in one earlier edit of that row, before the agent caught it while editing row 10 again. An error that survived three readers is better evidence for this section's point than a clean five-to-one would have been.

The human instances were all in document-writing. Across two prompts, the agent flagged that the draft text asserted more than the repo supported: four errors described as four error classes when they were two; format-limited items described as lacking a determinable size when they had one the format could not express; and a durable-goods share measured on priced items generalised to the whole category. It also flagged that the status banner claimed a module was built when only its extractor was, and offered either to correct the sentence or to build NUP next; the human chose to treat the sentence as the error rather than the code.

A further instance: the first draft of this very section contained two overclaims of its own, both flagged and corrected before it was written.

None of these was deliberate and each would have survived casual review. The lesson is that a verification step is not primarily a guard against model confabulation. It is a guard against whoever is writing the summary, and the direction of error is consistently toward claiming more.
