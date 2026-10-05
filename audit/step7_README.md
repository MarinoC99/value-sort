# Step 7 in-set audit: labelling guide

Written by the owner and committed on 4 October 2026, before any label exists in either
file. It is not edited once labelling starts; if a rule turns out to be ambiguous or wrong,
that is recorded in DECISIONS.md, not fixed here.

## Files

Both files are labelled against the same rules below, not file by file.

- `step7_contamination.csv`: 426 titles sampled from the kept and excluded sets of the eight
  pre-registered queries (prereg/STEP7.md, "Contamination audit").
- `step7_recall.csv`: 140 titles that contain the query words but fail the phrase match
  (prereg/STEP7.md, Deviation 1). Every row in this file failed the matcher by construction.

Fill in `in_set` with `yes` or `no`, from the title only (as pre-registered). Use `notes` as
rule 10 and the reporting rule below require.

## In-set labelling rules

The question for each title: would a shopper who typed this query consider this item
one of the things they are choosing between?

1. Form matters. The item must be the product in the form the query implies. A
   protein powder is a powder; a ready-to-drink shake is not. Baby wipes are wipes; a
   wipe warmer is not.
2. Variants of the same product are in: flavours, sizes, pack counts, unscented
   versions, store brands.
3. Accessories, containers and tools are out, even when sold for that product:
   funnels, shakers, dispensers, holders, cases, signs.
4. Sold-with bundles are in if the main item is the product. A monitor sold with a
   carrying case is a monitor; a case sold alone is not.
5. Bulk and case quantities are in. "48 rolls per case" is toilet paper.
6. Adjacent supplement types are out unless the query names them. Collagen, BCAA,
   mass gainers and creatine are not protein powder.
7. Products merely containing the ingredient are out. A mango powder sold for protein
   smoothies is not a protein powder; a multivitamin containing vitamin D is not
   vitamin D.
8. Vitamin D3 is a different product from plain vitamin D. Out.
9. Dish soap and dishwasher detergent are different products. Out.
10. If genuinely uncertain, label "no" and note it in the notes column.

## Recorded before labelling

**Rule 8 and the short-word fix.** Rule 8 means the pre-registered short-word fix will
register as contamination. The fix was built so that "vitamin d" matches "D3" and "D-3".
Allowing the digit suffix raises the phrase-matched set from 1,212 titles to 2,773 (2,766
kept after exclusions), and 2,059 of the 2,766 kept titles name D3 or D-3. That is a
measured result, not a reason to change either the rule or the labels.

**Reporting rule for uncertain rows.** Rule 10's bias is not symmetric. Labelling an
uncertain title "no" can only raise contamination, which is cautious, but can only lower
over-exclusion and recall loss, which flatters the matcher. Mark every uncertain row in the
notes column. All three measures are reported twice: with uncertain rows as labelled, and
with them excluded. Neither is the headline; both are shown.

Mark an uncertain row by starting its note with `UNCERTAIN`; any other note is a comment and
does not exclude the row.
