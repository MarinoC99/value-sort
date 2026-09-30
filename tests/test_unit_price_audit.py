import csv

import pytest

from value_sort import unit_price_audit as upa
from value_sort.schema import Item


def items(n=300):
    return [Item(parent_asin=f"A{i:04d}", title=f"t{i}", price=1.0 + i, average_rating=4.0,
                 rating_number=1, details={"Unit Count": f"{i}.0 Count"}) for i in range(n)]


def test_sample_is_deterministic_and_distinct():
    a, b = upa.audit_ids(items()), upa.audit_ids(list(reversed(items())))
    assert a == b and len(set(a)) == upa.SAMPLE_SIZE


def test_writes_empty_truth_and_extractor_fields(tmp_path):
    p = tmp_path / "labels.csv"
    assert upa.write_audit(items(), p) == 200
    rows = list(csv.DictReader(p.open(encoding="utf-8-sig")))
    assert len(rows) == 200 and all(r["truth"] == "" for r in rows)
    assert "unit_count" in rows[0] and rows[0]["unit_count"].endswith("Count")


def test_refuses_to_overwrite_labels(tmp_path):
    p = tmp_path / "labels.csv"
    upa.write_audit(items(), p)
    rows = list(csv.DictReader(p.open(encoding="utf-8-sig")))
    rows[5]["truth"] = "1 x 100 ct"
    with p.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    with pytest.raises(FileExistsError):
        upa.write_audit(items(), p)
