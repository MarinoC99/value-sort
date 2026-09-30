"""Unit-price audit set: 200 priced items for hand labelling, built before the extractor.

The labeller sees the title plus exactly the details fields the extractor is allowed to
read (EXTRACTOR_DETAIL_KEYS), so labels and extraction are judged on the same evidence.
The file is never overwritten once any truth cell has been filled in.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from value_sort.loader import load_items, priced
from value_sort.schema import Item

SAMPLE_SIZE = 200
SEED = 20260930
AUDIT_CSV = Path("audit/unit_price_labels.csv")

# The only details keys the extractor may read. Shown to the labeller for the same reason.
EXTRACTOR_DETAIL_KEYS = [
    "Unit Count",
    "Number of Items",
    "Item Package Quantity",
    "Size",
    "Item Weight",
    "Item Volume",
    "Liquid Volume",
    "Volume",
    "Sheet Count",
    "Number of Pieces",
    "Package Information",
    "Item Form",
]

LABEL_COLUMNS = ["truth", "notes"]


def column_name(key: str) -> str:
    return key.lower().replace(" ", "_")


def audit_ids(items: list[Item], n: int = SAMPLE_SIZE, seed: int = SEED) -> list[str]:
    """Deterministic simple random sample of parent_asins from the priced pool."""
    ids = sorted(i.parent_asin for i in items)
    return random.Random(seed).sample(ids, n)


def has_labels(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open(newline="", encoding="utf-8-sig") as f:
        return any((row.get("truth") or "").strip() for row in csv.DictReader(f))


def write_audit(items: list[Item], path: Path = AUDIT_CSV) -> int:
    if has_labels(path):
        raise FileExistsError(f"{path} already has labels; refusing to overwrite")
    by_id = {i.parent_asin: i for i in items}
    ids = audit_ids(items)
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ["audit_id", "parent_asin", "title", "price"] + [column_name(k) for k in EXTRACTOR_DETAIL_KEYS] + LABEL_COLUMNS
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # -sig so Excel reads UTF-8
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for n, a in enumerate(ids, 1):
            it = by_id[a]
            row = {"audit_id": n, "parent_asin": a, "title": it.title, "price": it.price}
            for k in EXTRACTOR_DETAIL_KEYS:
                v = it.details.get(k)
                row[column_name(k)] = "" if v is None else str(v)
            w.writerow({**row, "truth": "", "notes": ""})
    return len(ids)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="Health_and_Household")
    args = ap.parse_args()
    raw = Path("data/raw")
    items, _ = load_items(raw / f"meta_{args.category}.slim.parquet", raw / f"meta_{args.category}.manifest.json")
    n = write_audit(priced(items))
    print(f"Wrote {n} items to {AUDIT_CSV} (seed {SEED}); truth column empty.")


if __name__ == "__main__":
    main()
