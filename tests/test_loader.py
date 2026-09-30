import json

import pandas as pd
import pytest
from pydantic import ValidationError

from value_sort.loader import (
    EmptyTitle,
    LoadReport,
    MalformedRowsError,
    UnrecognisedPrice,
    load_items,
    parse_price,
    priced,
    row_to_item,
)
from value_sort.schema import Item


def raw_row(**over):
    row = {
        "parent_asin": "B000TEST01",
        "title": "Whey Protein, 2 lb",
        "price": json.dumps(24.99),
        "average_rating": json.dumps(4.5),
        "rating_number": json.dumps(120),
        "details": json.dumps({"Brand": "X"}),
    }
    row.update(over)
    return row


@pytest.mark.parametrize(
    "raw, expected",
    [
        (24.99, (24.99, None)),
        (7, (7.0, None)),
        (34355.69, (34355.69, None)),  # outliers kept as-is, never clipped
        (None, (None, "missing")),
        ("—", (None, "dash")),
        ("from 12.99", (None, "from_range")),
        ("from $10.00", (None, "from_range")),
        (0, (None, "non_positive")),
        (0.0, (None, "non_positive")),
        (-3.5, (None, "non_positive")),
    ],
)
def test_parse_price_known_cases(raw, expected):
    assert parse_price(raw) == expected


@pytest.mark.parametrize("raw", ["$12.99", "12.99", "N/A", "", True, [12.99], {"v": 1}])
def test_parse_price_unrecognised_fails_loudly(raw):
    with pytest.raises(UnrecognisedPrice):
        parse_price(raw)


def test_item_forbids_extra_fields():
    with pytest.raises(ValidationError):
        Item(parent_asin="A", title="t", price=1.0, average_rating=4.0,
             rating_number=1, details={}, categories=["x"])


def test_item_strict_no_coercion():
    with pytest.raises(ValidationError):
        Item(parent_asin="A", title="t", price=1.0, average_rating=4.0,
             rating_number="12", details={})


def test_item_allows_null_rating_fields():
    it = Item(parent_asin="A", title="t", price=None, average_rating=None,
              rating_number=None, details={})
    assert it.rating_number is None


def test_row_to_item_counts_null_reason():
    rep = LoadReport()
    it = row_to_item(raw_row(price=json.dumps("—")), rep)
    assert it.price is None and rep.price_null_reasons["dash"] == 1


@pytest.mark.parametrize(
    "bad",
    [
        {"average_rating": "{not json"},
        {"average_rating": json.dumps(7.0)},
        {"rating_number": json.dumps(-1)},
        {"rating_number": json.dumps("12")},
        {"parent_asin": ""},
        {"details": json.dumps([1, 2])},
        {"price": json.dumps("N/A")},
        {"details": None},
    ],
)
def test_row_to_item_structural_errors_raise(bad):
    with pytest.raises((ValueError, ValidationError)):
        row_to_item(raw_row(**bad), LoadReport())


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_empty_title_is_dropped_not_malformed(title):
    with pytest.raises(EmptyTitle):
        row_to_item(raw_row(title=title), LoadReport())


def test_row_missing_field_raises():
    row = raw_row()
    del row["details"]
    with pytest.raises(ValueError, match="missing field"):
        row_to_item(row, LoadReport())


def test_load_items_reports_every_bad_row(tmp_path):
    rows = [raw_row(parent_asin=f"A{i}") for i in range(3)]
    rows[0]["rating_number"] = json.dumps("x")
    rows[2]["average_rating"] = "{"
    p = tmp_path / "m.parquet"
    pd.DataFrame(rows).to_parquet(p)
    with pytest.raises(MalformedRowsError) as exc:
        load_items(p)
    assert [e[1] for e in exc.value.errors] == ["A0", "A2"]


def test_load_items_and_priced_filter(tmp_path):
    rows = [
        raw_row(parent_asin="A1"),
        raw_row(parent_asin="A2", price=json.dumps(None)),
        raw_row(parent_asin="A3", price=json.dumps(0)),
        raw_row(parent_asin="A4", title="Soap, 3 pack"),
        raw_row(parent_asin="A5", title="   ", price=json.dumps("—")),
        raw_row(parent_asin="A6", title=""),
    ]
    p = tmp_path / "m.parquet"
    pd.DataFrame(rows).to_parquet(p)
    items, rep = load_items(p)
    assert rep.rows_read == 6 and rep.items_loaded == 4 and rep.malformed_rows == 0
    assert rep.empty_titles_dropped == 2
    # A5's dash price is not counted: dropped rows don't contribute price reasons.
    assert rep.price_null_reasons == {"missing": 1, "non_positive": 1}
    assert rep.items_with_valid_price == 2
    assert [i.parent_asin for i in priced(items)] == ["A1", "A4"]


def test_manifest_with_bad_json_lines_fails(tmp_path):
    p = tmp_path / "m.parquet"
    pd.DataFrame([raw_row()]).to_parquet(p)
    man = tmp_path / "man.json"
    man.write_text(json.dumps({"unparseable_json_lines": 2}))
    with pytest.raises(MalformedRowsError):
        load_items(p, man)
