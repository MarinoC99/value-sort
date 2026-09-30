import json

import pytest

from value_sort import priors
from value_sort.schema import Item


def item(r, n):
    return Item(parent_asin=f"A{r}{n}", title="t", price=1.0, average_rating=r, rating_number=n, details={})


def test_compute_priors():
    p = priors.compute_priors([item(4.0, 10), item(5.0, 30), item(3.0, 20)])
    assert p["n_items"] == 3
    assert p["C_simple"] == pytest.approx(4.0)
    assert p["C_weighted"] == pytest.approx((40 + 150 + 60) / 60)
    assert p["m_median"] == 20.0


def test_compute_priors_skips_unrated():
    p = priors.compute_priors([item(4.0, 10), Item(parent_asin="B", title="t", price=1.0,
                                                   average_rating=None, rating_number=None, details={})])
    assert p["n_items"] == 1


def test_load_fallback_rejects_file_without_fallback_role(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "reports").mkdir()
    priors.fallback_path("X").write_text(json.dumps({"C_simple": 4.0, "m_median": 50}))
    with pytest.raises(ValueError, match="not a fallback"):
        priors.load_fallback("X")
