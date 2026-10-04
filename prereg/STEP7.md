# Step 7 pre-registration

> Committed on 4 October 2026, before any Step 7 matcher code exists. The machine-readable
> version, which the code reads, is [`config/step7_prereg.json`](../config/step7_prereg.json).
> Anything changed after matcher output exists is recorded below as a deviation, never edited
> silently. Decisions behind this: DECISIONS 49–53; SPEC Amendment 7.

## How much of this is genuinely pre-registered

**Only part of it.** The coherence rule and the plausibility guard were fitted to what the
Step 7 spike observed (CONSIDERATIONS §11). They are written down before any Step 7 code
exists, but they are not blind:

- The coherence rule was designed against **protein powder's** and **hand sanitizer's**
  behaviour in the spike, and the liquids handling follows hand sanitizer's oz/fl oz split.
- Coherence condition 3 (the count-spread limit) exists because of **toilet paper**.
- The plausibility guard's 10× thresholds were chosen with the spike's protein-powder tail
  errors in mind.

So results on protein powder, hand sanitizer and toilet paper are expected to look the way
the rules were built to make them look, and are not evidence that the rules work. **Dish
soap, baby wipes and creatine are the only genuine test of the rules**, and creatine is only
partly unexposed (its set size and priors appeared in the reverted Step 4 prototype; its
coverage was never measured). Vitamin d tests the short-word fix, not the coherence rule.

## Queries

| Query | Role | Prior exposure |
|---|---|---|
| protein powder | primary | Fitted: the coherence rule was designed against its spike behaviour |
| hand sanitizer | primary | Fitted: its oz/fl oz split shaped the liquids rule |
| toilet paper | **negative control**, expected no unit-price axis | Fitted: condition 3 exists because of it |
| blood pressure monitor | **negative control**, expected no unit-price axis | Spike |
| vitamin d | primary; tests the short-word fix | Spike set only (matcher defect); coverage never measured |
| dish soap | primary | None |
| baby wipes | primary | None |
| creatine | primary | Set size and priors seen in the reverted Step 4 prototype; coverage never measured |

If either negative control gets a unit-price axis, the coherence rule has failed for it, and
that is reported.

**Fallback.** If the contamination audit (480 labels) would stall Step 7, the query set drops
to five: toilet paper, blood pressure monitor, dish soap, baby wipes, creatine. That keeps
both negative controls and the unexposed queries. The fallback can only be taken before any
matcher output exists, and taking it is recorded here as a deviation.

## Matcher

- **Phrase match:** the query words must appear adjacent and in order, as whole words, ignoring
  case, with a hyphen or space allowed between words and an optional plural "s" on the last.
- **Short-word fix:** a query word of one or two characters matches only directly after the
  preceding query word, and may carry a digit suffix. "vitamin d" matches "Vitamin D",
  "Vitamin D3" and "Vitamin D-3", but not "Vitamins C, D, E" or "D-Mannose".
- **Exclusions** (whole words or phrases anywhere in the title):
  - every query: holder, case, keychain, sign(s), sticker(s), decal, empty, refillable
    bottle(s), stand, mount, extender, tongs, grab bar, rail, organizer;
  - protein powder and creatine: funnel, shaker, scoop;
  - blood pressure monitor: replacement cuff, cuff for;
  - hand sanitizer and dish soap: dispenser only, pump only;
  - baby wipes: warmer, dispenser.
- Other products that match the phrase (for example BCAA powders under protein powder) are not
  filtered; the contamination audit measures them.

## Unit-price axis: the coherence rule

A set gets a unit-price axis only if all three hold:

1. at least 30 items have an extracted pack size in a single dimension;
2. that dimension holds at least 80% of the set's extractions;
3. if the dimension is count, the set's 90th-percentile per-count price is at most 10× its
   10th-percentile per-count price.

Otherwise the set has no unit-price axis, and the failed condition is the reason the demo
shows. Units: weight in $/oz, volume in $/fl oz, count in $/count, on a log axis. The
extractor is unchanged (DECISIONS 51), so liquids listed in plain "oz" that fail the rule get
no axis.

**Condition 3 is untested.** The 10× threshold was chosen without looking at any of these
sets. It may also trip on sets with a genuine range of small and large packs, not only on
rolls-vs-sheets mixtures. Whichever way it goes, the result is reported with the per-count
spread behind it; a trip on toilet paper is not treated as confirmation that the rule
measures what it was meant to.

## Plausibility guard

- It flags; it never drops. A flagged item gets a distinct marker, is listed with its reason,
  and is left out of the quadrant medians and the axis scaling.
- An item is flagged if its unit price, or its extracted total package size, is more than 10×
  away from the set median in either direction.
- **Flagged items are reported in two groups: flagged and correct, flagged and wrong.** The
  10× rule will flag genuine sample packs, so the flag count must not later be read as an
  error count. Which group an item belongs to is decided by inspection and recorded.
- `Item Weight` is shown on the item card where it disagrees with the extracted size by more
  than 3×. It does not flag or veto anything; whether it should veto stays open
  (CONSIDERATIONS §11.9).

## Contamination audit

Run after the matcher is built and before any results are computed. For each query, 40
random titles from the kept set and 20 from the excluded set (seed 20261004) go to
`audit/step7_contamination.csv` with an empty `in_set` column, labelled yes/no by hand from the
title only. Reported per query, each with a 95% Wilson interval:

- **contamination:** kept titles labelled "no";
- **over-exclusion:** excluded titles labelled "yes".

Any query whose kept-set contamination point estimate is above 10% gets a visible note in the
demo.

## Step 8 definitions

- **Quadrants** split at the set medians of items that have both axes, excluding flagged items.
- **Clearly off the diagonal:** one axis in the top third and the other in the bottom third,
  by within-set percentile rank.
- **Star sort:** average rating descending, then rating count descending, then product ID.

## Publication (Step 9)

At most 50 items per set are published: a seeded random sample of the kept set (seed
20261004, the same date-as-seed convention as the Step 5 audit). The page states "50 of N".
Step 8 measures use the full set. A demo-specific data notice and removal route apply
(DECISIONS 53).

## Deviations

None yet.
