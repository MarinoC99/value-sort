# Step 7 spike: findings (in progress)

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
