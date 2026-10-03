# Build plan and working agreement

> **How this file came to exist.** Until 2 October 2026 the build plan and the working
> agreement below existed only as text in the chat session that drove the build. They were
> never committed. Two places in this repository cite them: DECISIONS.md's header
> ("Judgment calls not specified in SPEC.md or the build instructions") and
> CONSIDERATIONS.md §5 ("Step 8 of the build brief forbids it explicitly"). Until now, both
> were citing something unversioned. This file is a transcription from that chat, committed
> on 2 October 2026. The plan text is reproduced as given; changes made since are listed
> under [Amendments](#amendments) rather than edited into it, the same way SPEC.md keeps
> superseded claims visible.

## The plan, as given

```
I'm an MBA student building a portfolio project. Read SPEC.md in the repo root
before doing anything — it is the contract. If anything you're about to build
contradicts it, stop and ask instead of improvising.

## Working agreement (read first, applies to every step)
- Never fabricate a number. If a metric requires data we don't have, print
  "NOT MEASURABLE WITH THIS DATA" and say what would be needed.
- Stop and ask me before: downloading anything over 500MB, adding a dependency
  not already in pyproject.toml, or making an API call that costs money.
- Work in vertical slices. After each numbered step below, stop, show me what
  runs, and wait for my go-ahead. Do not chain steps.
- Commit after each step with a message describing the decision, not the diff.
- No scraping of amazon.com. Public dataset only.
- When you make a judgment call I didn't specify, add it to DECISIONS.md with a
  one-line rationale.
- Modules ship in order: CAR, then unit price, then attributes. Each is a
  complete stopping point. Do not begin the attribute module until I have seen
  the unit-price precision number and told you to continue.

## Step 1 — Scaffold
Python 3.11, uv for deps, src/ layout, pytest. Create DECISIONS.md and a README
stub. Add a Makefile with: make data, make build, make eval, make demo.

## Step 2 — Data
Pull ONE category from the Hugging Face dataset McAuley-Lab/Amazon-Reviews-2023
— configs raw_meta_<Category> and raw_review_<Category>. Default to
Health_and_Household. Cache to data/raw/, gitignored.
Write a profiling script that reports, before any modeling: row counts, % of
items with a non-null price, % with rating_number, price distribution, and the
category mean rating and median rating count. Show me this before Step 3.

## Step 3 — Schema contract
Define a typed Item record (pydantic) with exactly the fields downstream code
may use: parent_asin, title, price, average_rating, rating_number, details.
Anything not in this record is off-limits to later steps. Write the loader to
emit these and fail loudly on malformed rows rather than silently dropping them.
Report the drop count.

## Step 4 — CAR module
Implement Credibility-Adjusted Rating per the formula in SPEC.md. m and C come
from the Step 2 profile, not hardcoded. Include a sensitivity harness that
reports how the top-20 changes at m = 25, 120, and 500. Unit tests for the
edge cases: zero ratings, one rating, rating_number null.

## Step 5 — Unit price extraction (build the audit before the extractor)
First, sample 200 items and write them to audit/unit_price_labels.csv with an
empty truth column for me to fill in by hand. Then build the extractor that
parses pack count and size from title + details. Then score the extractor
against my labels and print precision.
Hard rule: if confidence is below threshold, return None and flag the item.
Never guess a pack size. Do not proceed to Step 6 until precision is reported.

## Step 6 — Attribute extraction (LLM)
Define a fixed per-category attribute schema (5-8 attributes) in a YAML file I
can edit. For each of the top N items by review count, send a sample of review
text to an LLM and extract attribute sentiment scores.
Requirements: cache every response to disk keyed by item id so re-runs cost
nothing; cap total spend and tell me the estimate before the first call; every
extracted attribute must include the review sentence that supports it.
Start with N=50 so I can inspect output before scaling.

## Step 7 — Composite scorer
Combine per SPEC.md with weights in a config file, not in code. Standardize
within the result set, not globally. Expose a single function:
rank(query, candidate_items, weights) -> ordered list with a per-item
explanation string.

## Step 8 — Offline evaluation
Compute only what SPEC.md's Limitations section allows: Kendall's tau between
default and re-ranked order, share of top-10 positions changed, and the
extraction precision from Step 5. Output eval/results.md.
Do not compute or imply a lift in conversion, revenue, or satisfaction.

## Step 9 — Demo
A single self-contained HTML page: category picker, weight sliders, side-by-side
default vs. Value Sort ordering with position deltas, and the explanation string
visible per item. No build step, no framework, deployable as a static file.

## Step 10 — README
Write it for a hiring manager, not a developer. Lead with the problem and the
finding. Include the honest limitations section. Then setup instructions.

## Added later in the conversation (after the Step 4 matcher was reverted)
- Never build a component that a later step owns, even a minimal version. If a
  step needs something that doesn't exist yet, stop and ask.
```

## Amendments

Changes to the plan made after it was given. The plan text above is not edited; each change
points to the record that made it. Steps not listed have no recorded amendment.

**Step 2 — Data**
- The data is fetched by streaming the raw JSONL file with `huggingface_hub`, not through the
  `datasets` configs named in the plan. (DECISIONS #47, logged retrospectively)
- Metadata only, streamed: only the six contract fields are written to a slim Parquet, and
  the 2.47 GB source JSONL is never stored. (DECISIONS #5)
- `categories` is not kept in the slim file. (DECISIONS #6)
- The `raw_review_<Category>` pull did not happen in Step 2. If Step 6 is reached, reviews
  are to be streamed and filtered to the top-N items, never downloaded in full.
  (DECISIONS #10, filed under Step 6)

**Step 3 — Schema contract**
- Price rules: "—", "from $X" and values of $0 or less become null with a counted reason;
  outliers are kept unclipped; price strings matching no known pattern fail loudly.
  (DECISIONS #16, #17)
- Rows with empty or whitespace-only titles are dropped at load and counted, not treated as
  malformed. (DECISIONS #18)
- Only items with a valid price above zero enter ranking. (DECISIONS #14)

**Step 4 — CAR module**
- "m and C come from the Step 2 profile" is superseded: C and m are computed over the
  candidate set at rank time, with stored priced-set priors used only as a flagged fallback
  when a set has fewer than 30 items, counted as rated items. (DECISIONS #12, which is
  SPEC.md Amendment 1; DECISIONS #21, #26)
- The sensitivity check was first extended to vary C three ways (DECISIONS #15); varying C
  over the candidate-set mean was then deferred to Step 7 (DECISIONS #22).
- The sensitivity check runs over the whole priced pool, compared pairwise, because no
  candidate sets exist yet. (DECISIONS #23)
- m = 50 was added to the sweep, making it m = 25, 50, 120 and 500. (DECISIONS #48, logged
  retrospectively)

**Step 5 — Unit price extraction**
- Items whose size is a length the truth format can't express are reported as a separate
  category beside the pre-registered rule, never instead of it. (DECISIONS #39)
- Open questions raised by the audit: whether unit price should support length units
  (DECISIONS #40), and the paper-bowls labelling-guide gap (DECISIONS #41).

**Step 6 — Attribute extraction**
- Not started. Reviews, if needed, are to be streamed and filtered to the top-N items.
  (DECISIONS #10)

**Step 7 — Composite scorer**
- Candidate sets are to be built by title keyword match, with no leaf categories and no
  re-stream. (DECISIONS #13)
- A throwaway spike tested the Step 7 idea before Step 7 proper, on the unmerged branch
  `spike/step7`, under its own rules: everything it produced is indicative only, and none
  of it may be cited in README.md, SPEC.md or the portfolio page until re-measured. Its
  questions, and indicative figures as a deliberate exception, are recorded in
  CONSIDERATIONS.md §11. There is no DECISIONS entry for the spike itself; DECISIONS #27 and
  #28 point to it.
