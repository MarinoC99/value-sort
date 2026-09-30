# Unit-price audit: labelling guide

`unit_price_labels.csv` holds 200 priced items drawn at random (fixed seed) from the
331,095 priced items in Health & Household. It was created **before** the extractor
existed, and the extractor was developed on a separate sample that doesn't overlap it.

Fill in the `truth` column by hand. `notes` is optional.

## Label using only the columns in the file

The columns are the title plus the exact `details` fields the extractor is allowed to
read. Please don't look products up on Amazon: the listing may have changed since the
2023 snapshot, and a label based on information the extractor can't see doesn't measure
the extractor.

## Format for `truth`

One of three forms:

| Form | Meaning | Examples |
|---|---|---|
| `COUNT x SIZE UNIT` | What the price buys: COUNT packages, each containing SIZE UNIT. | `1 x 16 fl oz` · `3 x 8 oz` · `1 x 100 ct` · `2 x 500 ml` · `6 x 1 ct` |
| `NONE` | A human can't determine the pack size from these fields. | Title and details are silent or contradict each other. |
| `N/A` | Unit price isn't meaningful: a single durable item. | Blood pressure monitor, heating pad, scale. |

Units: `oz` (weight), `fl oz`, `lb`, `g`, `kg`, `mg`, `ml`, `l`, `ct` (count: tablets,
capsules, bags, wipes, sheets, pods, etc.).

Rules of thumb:
- **Weight vs fluid ounces:** use `fl oz` only when the text says fluid ounces or the
  product is clearly a liquid sold by volume. Otherwise use `oz`.
- **Count products:** "Vitamin D3, 2 bottles of 120 softgels" → `2 x 120 ct`.
- **Size beats count if both are given for one package:** "Wipes, 3 packs of 75" →
  `3 x 75 ct`. "Protein powder, 2 lb (32 servings)" → `1 x 2 lb` (servings aren't a unit here).
- **Shipping weight is not net weight.** If `item_weight` looks like the weight of the
  box rather than the contents, and nothing else gives the size, use `NONE`.
- **When unsure between a label and `NONE`, choose `NONE`.** The extractor is supposed
  to abstain in exactly those cases.

## How it is scored

- The extractor either returns a pack size or abstains (returns None, and the item is
  flagged in the UI and keeps its listed price).
- **Precision** = correct ÷ (items where the extractor returned a pack size). This is
  the SPEC's ≥ 90% guardrail number.
- **Correct** = same dimension (weight / volume / count) and total quantity
  (COUNT × SIZE, converted to a base unit) within 1%. Total quantity is what unit price
  uses, so `2 x 8 oz` and `1 x 16 oz` both count as correct for a 16 oz total. An exact
  COUNT and SIZE match is reported separately.
- The extractor returning a pack size where truth is `NONE` counts as **wrong**.
- **Coverage** (share of items where the extractor returns a pack size) is reported
  alongside precision, so abstaining on everything can't inflate precision.
- `N/A` items are reported separately. Precision is given both with and without them,
  because trivial `1 x 1 ct` cases would otherwise inflate it.
