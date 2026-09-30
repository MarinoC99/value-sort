import csv

import pytest

from value_sort.schema import Item
from value_sort.unit_price_score import LabelError, judge, parse_truth, read_labels, score, wilson
from value_sort.unit_price import extract


def it(asin, title, **details):
    return Item(parent_asin=asin, title=title, price=10.0, average_rating=4.0, rating_number=10, details=details)


@pytest.mark.parametrize("s, kind", [("1 x 16 fl oz", "size"), ("3 x 8 oz", "size"), ("NONE", "none"),
                                     ("n/a", "na"), (" 2 x 500 ML ", "size"), ("1 x 100 ct", "size")])
def test_parse_truth(s, kind):
    assert parse_truth(s).kind == kind


@pytest.mark.parametrize("s", ["16 oz", "1x", "two x 8 oz", "1 x 8 stones"])
def test_parse_truth_rejects_bad_labels(s):
    with pytest.raises(LabelError):
        parse_truth(s)


def test_total_quantity_rule():
    e = extract(it("A", "Shampoo 16 oz"), 0.7)
    assert judge(e, parse_truth("2 x 8 oz")) == "correct"  # same total
    assert judge(e, parse_truth("1 x 1 lb")) == "correct"  # 453.6 g vs 453.6 g
    assert judge(e, parse_truth("1 x 16 fl oz")) == "wrong"  # different dimension
    assert judge(e, parse_truth("NONE")) == "wrong"
    assert judge(e, parse_truth("N/A")) == "wrong"


def test_abstention_is_not_scored_as_wrong():
    e = extract(it("A", "Heating Pad"), 0.7)
    assert judge(e, parse_truth("1 x 1 ct")) == "abstained"


def test_refuses_partial_labels(tmp_path):
    p = tmp_path / "l.csv"
    with p.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["audit_id", "parent_asin", "title", "truth"])
        w.writeheader()
        w.writerow({"audit_id": 1, "parent_asin": "A", "title": "t", "truth": "NONE"})
        w.writerow({"audit_id": 2, "parent_asin": "B", "title": "t", "truth": ""})
    with pytest.raises(LabelError, match="1 of 2"):
        read_labels(p)


def test_score_end_to_end():
    items = {"A": it("A", "Lutein 120 Softgels"), "B": it("B", "Heating Pad"),
             "C": it("C", "Shampoo 16 oz"), "D": it("D", "Soap 3 oz")}
    rows = [{"audit_id": "1", "parent_asin": "A", "title": "", "truth": "1 x 120 ct"},
            {"audit_id": "2", "parent_asin": "B", "title": "", "truth": "N/A"},
            {"audit_id": "3", "parent_asin": "C", "title": "", "truth": "1 x 16 fl oz"},
            {"audit_id": "4", "parent_asin": "D", "title": "", "truth": "NONE"}]
    r = score(rows, items, 0.7)
    assert r["coverage"] == 0.75
    assert r["precision_all"]["correct"] == 1 and r["precision_all"]["returned"] == 3
    assert r["returned_where_truth_none"] == 1 and not r["passes_guardrail"]


def test_wilson_bounds():
    lo, hi = wilson(90, 100)
    assert 0.82 < lo < 0.83 and 0.94 < hi < 0.95
