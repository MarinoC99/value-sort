"""Load the slim metadata into validated Item records.

Two kinds of problem, handled differently:

* Empty or whitespace-only titles are dropped and counted. Such an item cannot be
  candidate-matched or pack-size parsed, so it cannot take part in ranking.
* Known price conditions ("—", "from $X", <= 0, missing) are data, not errors. The price
  becomes None and the reason is counted.
* Structural problems (bad JSON, missing or wrongly typed field, unrecognised price
  format) are errors. Every row is checked, then the load raises with the full list, so
  one run shows every problem instead of only the first.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from value_sort.schema import Item

_RANGE = re.compile(r"^from \$?\d+(\.\d+)?$")
_MISSING = object()


class MalformedRowsError(Exception):
    def __init__(self, errors: list[tuple[int, str, str]]):
        self.errors = errors
        head = "\n".join(f"  row {i} ({asin}): {msg}" for i, asin, msg in errors[:50])
        more = f"\n  ... and {len(errors) - 50} more" if len(errors) > 50 else ""
        super().__init__(f"{len(errors)} malformed row(s):\n{head}{more}")


class UnrecognisedPrice(ValueError):
    pass


class EmptyTitle(Exception):
    """Not an error: the row is well-formed but cannot participate in ranking."""


def parse_price(raw: object) -> tuple[float | None, str | None]:
    """Return (price, null_reason). Raises UnrecognisedPrice for anything unexpected."""
    if raw is None:
        return None, "missing"
    if isinstance(raw, bool):
        raise UnrecognisedPrice(f"boolean price {raw!r}")
    if isinstance(raw, (int, float)):
        if raw <= 0:
            return None, "non_positive"
        return float(raw), None
    if isinstance(raw, str):
        s = raw.strip()
        if s == "—":
            return None, "dash"
        if _RANGE.match(s):
            return None, "from_range"
    raise UnrecognisedPrice(f"unrecognised price {raw!r}")


@dataclass
class LoadReport:
    rows_read: int = 0
    items_loaded: int = 0
    malformed_rows: int = 0
    price_null_reasons: Counter = field(default_factory=Counter)
    items_with_valid_price: int = 0
    empty_titles_dropped: int = 0

    def as_dict(self) -> dict:
        return {
            "rows_read": self.rows_read,
            "items_loaded": self.items_loaded,
            "malformed_rows_dropped": self.malformed_rows,
            "price_null_reasons": dict(self.price_null_reasons),
            "price_null_total": sum(self.price_null_reasons.values()),
            "items_with_valid_price": self.items_with_valid_price,
            "empty_titles_dropped": self.empty_titles_dropped,
        }


def _decode(value: object, name: str) -> object:
    if value is None:
        return _MISSING
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError) as e:
        raise ValueError(f"{name}: bad JSON ({e})") from None


def row_to_item(row: dict, report: LoadReport) -> Item:
    required = ["parent_asin", "title", "price", "average_rating", "rating_number", "details"]
    missing = [f for f in required if f not in row]
    if missing:
        raise ValueError(f"missing field(s) {missing}")

    decoded = {f: _decode(row[f], f) for f in ["price", "average_rating", "rating_number", "details"]}
    absent = [f for f, v in decoded.items() if v is _MISSING]
    if absent:
        raise ValueError(f"field(s) absent in source {absent}")

    if isinstance(row["title"], str) and not row["title"].strip():
        raise EmptyTitle
    price, reason = parse_price(decoded["price"])
    item = Item(
        parent_asin=row["parent_asin"],
        title=row["title"],
        price=price,
        average_rating=decoded["average_rating"],
        rating_number=decoded["rating_number"],
        details=decoded["details"],
    )
    if reason:
        report.price_null_reasons[reason] += 1
    return item


def load_items(path: Path, manifest: Path | None = None) -> tuple[list[Item], LoadReport]:
    if manifest is not None and manifest.exists():
        bad_json = json.loads(manifest.read_text())["unparseable_json_lines"]
        if bad_json:
            raise MalformedRowsError([(-1, "-", f"{bad_json} source line(s) were not valid JSON; see {manifest}")])

    df = pd.read_parquet(path)
    report = LoadReport(rows_read=len(df))
    items: list[Item] = []
    errors: list[tuple[int, str, str]] = []

    for i, row in enumerate(df.to_dict("records")):
        try:
            items.append(row_to_item(row, report))
        except EmptyTitle:
            report.empty_titles_dropped += 1
        except (ValueError, ValidationError) as e:
            msg = str(e).replace("\n", " ")
            errors.append((i, row.get("parent_asin") or "?", msg))

    report.malformed_rows = len(errors)
    if errors:
        raise MalformedRowsError(errors)

    report.items_loaded = len(items)
    report.items_with_valid_price = sum(it.price is not None for it in items)
    return items, report


def priced(items: list[Item]) -> list[Item]:
    """Items eligible for ranking: valid price > 0. Unpriced items are not to enter a candidate set."""
    return [it for it in items if it.price is not None]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="Health_and_Household")
    args = ap.parse_args()
    raw = Path("data/raw")
    items, report = load_items(
        raw / f"meta_{args.category}.slim.parquet",
        raw / f"meta_{args.category}.manifest.json",
    )
    out = report.as_dict()
    Path("reports").mkdir(exist_ok=True)
    Path(f"reports/load_{args.category}.json").write_text(json.dumps(out, indent=2))

    print(f"Rows read:                 {out['rows_read']:,}")
    print(f"Malformed rows dropped:    {out['malformed_rows_dropped']:,}")
    print(f"Empty titles dropped:      {out['empty_titles_dropped']:,}")
    print(f"Items loaded:              {out['items_loaded']:,}")
    print("Price set to null, by reason:")
    for k in ["missing", "dash", "from_range", "non_positive"]:
        print(f"  {k:<14} {out['price_null_reasons'].get(k, 0):>9,}")
    print(f"  {'total':<14} {out['price_null_total']:>9,}")
    print(f"Survive price > 0 filter:  {out['items_with_valid_price']:,} "
          f"({100 * out['items_with_valid_price'] / out['items_loaded']:.2f}%)")


if __name__ == "__main__":
    main()
