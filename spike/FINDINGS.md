# Step 7 spike: findings

> **INDICATIVE ONLY.** Everything here comes from throwaway spike code on branch
> `spike/step7`. No number in this file is a project result, and none may be cited in
> SPEC.md, README.md, DECISIONS.md or CONSIDERATIONS.md. (Same rule as DECISIONS #22, #28.)

Matcher under test: title keyword match per DECISIONS #13. Every query word must appear
in the title as a whole word, case-insensitive, over the 331,095 priced items. Queries were
pre-registered in `queries.txt` before the matcher was written.

## Finding 1: matcher defect on single-letter query words ("vitamin d")

Whole-word matching on the single letter "d" both over-matches and under-matches:
- It catches "D" in "D-Mannose", "Vitamins C, D, E" in multivitamins, and a book.
- It misses "Vitamin D3", because "D3" isn't the word "d". 1,491 of 1,998 priced titles
  containing "vitamin D3" are not in the set.

This is a defect in the matching rule, not a finding about the data. Nothing computed on
that set would be interpretable, so "vitamin d" is excluded from Tasks 2-4.

## Finding 2: candidate sets mix in accessories and other products

Reading 40 random titles per query, the agent flagged items that aren't the queried product:

| Query | Flagged (agent) | Blind-judge majority | Agreement |
|---|---|---|---|
| protein powder | 4/40 | 8/40 | 36/40 |
| toilet paper | 15/40 | 14/40 | 39/40 |
| blood pressure monitor | 7/40 | 7/40 | 40/40 |
| hand sanitizer | 10/40 | 10/40 | 40/40 |

Examples: toilet-paper tongs, grab rails, foam, signs; empty sanitizer bottles, holders,
floor stands; replacement BP cuffs and cases; a protein-powder funnel. The flags are the
agent's own sample-level judgments, not a classifier. Three blind LLM judges agreed on
155/160; they flagged collagen powders as not protein powder where the agent didn't, and
didn't flag a toilet-paper holder that comes with boxed tissue, which the agent did.
Not extrapolated to the full sets.

## Finding 3: accessories do not fail open, and they feed the extractor its known failure mode

On the sampled titles (agent's own flags, not extrapolated), flagged items got a pack size
at about the same rate as real products: **12/36 (33%) vs 46/124 (37%)**. Contamination and
coverage do not cancel; accessories reach the unit-price axis.

One flagged toilet-paper item, a grab bar with a paper holder, was read as `1 x 250 lb`
from its load rating. That is the same error shape as the Step 5 transfer bench
("400 lbs Weight Capacity"): a number describing the product rather than what the price
buys. Accessory contamination therefore structurally feeds the extractor its known failure
mode. **The matcher needs a filter before Step 7 proper.**

## Finding 4: toilet paper's "ct" is incoherent

Count is 95% of toilet-paper extractions, but "ct" means rolls on some listings, sheets on
others, and mega rolls aren't regular rolls. Sampled values run from `1 x 60 ct` (a gag
roll) to `1 x 11520 ct` (sheets in 36 mega rolls). 37% coverage that can't support a unit
price. Excluded from Task 3.

## Finding 5 (known extractor artifact, not fixed): oz vs fl oz in hand sanitizer

Hand sanitizer listed in plain "oz" is a liquid, but the extractor treats plain "oz" as
weight by design, so the set splits into volume (117), weight (88) and count (77). Not
fixed during the spike: changing the extractor would make Task 2 and Task 3 numbers come
from different code.

## Finding 6: the two axes are near-independent

Within each set, z(CAR) and −z(ln unit price) are close to uncorrelated: Spearman ρ =
**0.10** (protein powder, n = 1,032 with a unit price) and **0.13** (hand sanitizer,
n = 117). The headline for off-diagonal structure is **121 clearly off-diagonal items**
(|z| > 0.5 on both axes) in protein powder. The quadrant counts (264 / 211 / 284 / 273) are
four near-equal quarters, which is roughly what any uncorrelated pair produces; they
mostly restate ρ and aren't separate evidence. The two axes carry different information,
so the matrix isn't decoration.

## Finding 7: unit-price tails are extraction errors

In protein powder, 21 of 1,032 items have an extracted package weight under 60 g, with
z(value) down to **−7.6**. *[Corrected after per-item check: not all 21 are errors. By the
agent's reading about 14 are per-serving grams read as package size; 6 are genuine small
items (3 sample packs, 3 small spirulina jars, the latter contamination rather than
extraction errors); 1 is unclear. Three more errors sit in the heavy tail (grams written as
ounces). About 17 errors in all, roughly 1.6%.]* The cheapest tail is `Unit Count` written in grams but
labelled ounces ("454.0 Ounce" on a 45-serving collagen). The priciest tail is per-serving
protein grams read as package size ("19g Per Serving", "17g Whey", "3g x 90"). The
quadrant result survives removing them (ρ = 0.096, 47.9% off-diagonal), but **a weighted
sum would be dominated by them**.

*[Corrected: the original said `Item Weight` contradicted every case. Of the ~17 errors it
contradicted 12, carried the same wrong value in 2, and was absent in 3. In the heavy tail it
would also have vetoed one correct extraction: a multi-pack where `Item Weight` is per unit.]*
DECISIONS #35 excluded it as a *source*. Using it as a *veto* on implausible extractions
is a different mechanism. It is now an open decision for Step 7, not a change to make here.

## Finding 8: dominant-dimension unit price works for protein powder, poorly for hand sanitizer

Option 1 (unit price only in the set's dominant dimension; everything else fails open):
- **Protein powder:** weight is 96% of extractions, so 1,032 of 1,625 items (64%) get a
  comparable $/oz.
- **Hand sanitizer:** only 117 of 652 (**18%**) get a unit price. 88 items are dropped for
  being extracted in "oz". *[Corrected: the original said 88 real products. By the agent's
  reading about 76 are sanitizer; about 12 are holders, a pump holster and a skin ointment.
  The holders' "1 oz" is the capacity of the bottle they fit, the Step 5 error shape again.]* Accessories were filtered only as a side
  effect: all 10 sampled accessories had count extractions, the non-dominant dimension.

## Finding 9: CAR per query (the #28 question, on a real matcher for the first time)

| Query | Set | C | m | CAR top-20 ∩ star-sort top-20 | Median ratings, star-sort top 20 | Median ratings, CAR top 20 |
|---|---|---|---|---|---|---|
| protein powder | 1,625 | 4.2948 | 123 | **0 / 20** | 8.5 | 4,544.5 |
| hand sanitizer | 652 | 4.3724 | 54 | **0 / 20** | 6.5 | 1,519 |
| *toilet paper (supplementary)* | 736 | 4.2099 | 109 | 1 / 20 | 2 | 2,517 |
| *blood pressure monitor (supplementary)* | 484 | 4.1973 | 153.5 | 8 / 20 | 132 | 1,197 |

Star sort = average_rating descending, ties broken by rating count (same as the Step 4
sweep). Supplementary rows weren't requested for Task 4. They're included because CAR doesn't
depend on the unit-price problems that excluded those queries from Task 3, but their sets
are heavily contaminated (Finding 2).

**CAR does not behave differently across protein powder and hand sanitizer**, even though
m = 123 and m = 54 straddle the transition the Step 4 sweep found. In both, the star-sort
top 20 is all 5.0-star items with single-digit rating counts, and CAR replaces all of them
at every m from 50 up, and all but one at m = 25 (overlap 1, 0, 0, 0 at m = 25/50/120/500
for protein powder; 0 throughout for hand sanitizer). *[Corrected: the original said
"every one at every m tested".]* The Step 4 transition was a property of the 331,095-item pool, which
has enough 5.0-star items with hundreds of ratings to survive a small m. Sets of this size
don't. The #28 worry, CAR near-inert on some sets, didn't appear in these two.

Where behaviour did differ is the supplementary blood-pressure set: its star-sort top 20 is
less thin (median 132 ratings, 10 of 20 at 5.0), so CAR keeps 8 of 20 and m matters
(15 → 4 overlap from m = 25 to 500). What separates the queries is how thin the star-sort
top is, not where m falls.

Two further checks:
- **m matters less within a set than across the pool.** CAR's own top 20 at the set's m
  keeps 14–20 of 20 items at m = 25 or 50 and 13–18 at m = 500, across the four sets. Over
  the whole pool, the top 20 was replaced entirely between m = 25 and m = 120.
- **CAR is not a popularity sort.** Its top 20 shares 3/20 (protein powder) and 8/20 (hand
  sanitizer) with the 20 most-reviewed items. Across each set it tracks the star rating
  (Spearman ≈ 0.88) far more than the rating count (0.39–0.54).

---

## Summary

### What was tested

Whether Step 7's idea, ranking a candidate set on two standardized axes (credibility-adjusted
rating and log unit price), has a blocker that kills it. Five queries were pre-registered:
protein powder, toilet paper, vitamin d, blood pressure monitor, hand sanitizer. Throwaway
code covered:
- Task 1: the DECISIONS #13 title-keyword matcher.
- Task 2: the existing Step 5 extractor run over each candidate set.
- Task 3: CAR with set priors (#12) against dominant-dimension unit price, for two sets.
- Task 4: CAR per query.

No composite score was built.

### What came back

| Question | Result (indicative) |
|---|---|
| Does the matcher produce comparable products? | No. One query is broken by the rule itself (Finding 1). The rest mix in accessories and other products, from 4/40 to 15/40 sampled (Finding 2). |
| Do accessories fail open on their own? | No: 33% vs 37% get a pack size, and they feed the extractor its known error shape (Finding 3). |
| Does a unit-price axis exist? | Cleanly for 1 of 4 sets (protein powder, 64%). Weak for hand sanitizer (18%), incoherent for toilet paper, absent for blood pressure monitors (1.7%) (Findings 4, 5, 8). |
| Are the two axes redundant? | No: ρ ≈ 0.10–0.13, with 121 clearly off-diagonal items in protein powder (Finding 6). |
| Is standardized unit price safe to put in a weighted sum? | Not as built: roughly 1.6% extraction errors reach z = −7.6 (Finding 7). |
| Does CAR do anything per query? | Yes, decisively in both requested sets, and not as a popularity proxy. The feared inertness didn't appear (Finding 9). |

### What it implies for Step 7

**No single result kills the two-axis approach.** The axes are independent where both
exist, and CAR does real work inside candidate sets. But three problems must be resolved
before Step 7 proper, and each is a decision, not a tweak:

1. **The matcher needs a contamination filter and a fix for short tokens.** As written, it
   produces candidate sets in which accessories reach the unit-price axis and trigger the
   extractor's known failure mode. This is the closest thing to a blocker the spike found.
   Ranking contaminated sets means ranking tongs against toilet paper.
2. **Unit-price tails need a guard before any weighting.** Options include a plausibility
   veto (`Item Weight` as veto is now an open decision; it would miss some errors and reject
   at least one correct multi-pack), robust scaling, or both. Without one, a small share of
   errors can dominate a weighted sum.
3. **"No usable unit-price axis" is the common case, not the edge case.** In 3 of 4 tested
   sets the axis is weak, incoherent or absent. Step 7 must decide how fail-open items
   enter a weighted sum (still undecided, deliberately) and how a query with no unit-price
   axis renormalizes. That decision can no longer be deferred past Step 7's design.

Also for the record: the Step 4 whole-pool m-sweep is the wrong place to argue about m
(#27, #28). Inside candidate sets the transition it found didn't reappear, and m mattered
moderately rather than decisively. Any defence of the default m should be made on
candidate sets.

### What should NOT be concluded from these numbers

- **None of these numbers are project results.** The matcher is throwaway and must change
  (point 1 above). Every set size, prior, coverage figure and overlap here will change with
  it. Nothing from this file goes into SPEC.md, README.md, DECISIONS.md or
  CONSIDERATIONS.md (DECISIONS #22, #28).
- **Four queries are not the category.** They were chosen by hand, not sampled, and one of
  five was dropped. "1 of 4 sets has a clean unit-price axis" describes these four.
- **Independent axes don't show that Value Sort helps anyone.** Low ρ means the matrix
  isn't redundant; it says nothing about shopper benefit.
- **CAR displacing the star sort doesn't show that CAR is better.** The star sort here is a
  constructed baseline (rating, then count), not Amazon's ordering.
- **The accessory rates come from 160 sampled titles** judged by the agent, checked by three
  LLM judges. They are not a classifier and are not extrapolated to full sets.
- **The tail-error rate (~1.6%) is not extractor precision.** Precision is the Step 5 audit
  (93.1% on a random priced sample). This is a different population (one query's set) and a
  different question (implausible weights, not hand-checked labels).
- **"CAR is not inert" holds for these sets only.** The supplementary blood-pressure set
  already behaves differently; #28 is answered for two sets, not in general.
- **Small n for hand sanitizer.** ρ = 0.13 rests on 117 items.
- **The Task 3 plot was not visually inspected by the agent.** The browser couldn't open
  local files; placement was checked programmatically only.

## Corrections log

Four statements in this file were overclaims by the agent, found while preparing the
CONSIDERATIONS.md §11 entry and corrected in place (marked *[Corrected …]*):
1. "21 implausible weights" were treated as 21 errors; about 14 are.
2. "`Item Weight` contradicted every case" was false (12 of ~17).
3. "88 real products dropped" included about 12 holders and other items.
4. "CAR replaces every one at every m" was contradicted by the file's own m = 25 figure.

Each claimed more than had been checked.
