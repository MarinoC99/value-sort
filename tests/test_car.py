"""CAR edge cases. Zero, one, and null rating counts do not occur in the Health_and_Household
data (every item has rating_number >= 1), so these are synthetic inputs."""

import pytest

from value_sort.car import car, priors_for, rank_by_car
from value_sort.schema import Item

C, M = 4.25, 50


def item(asin, r, n, title="Whey Protein Powder"):
    return Item(parent_asin=asin, title=title, price=10.0, average_rating=r, rating_number=n, details={})


# --- the three required edge cases -------------------------------------------------

def test_zero_ratings_returns_prior_exactly():
    assert car(R=None, v=0, C=C, m=M) == C
    assert car(R=5.0, v=0, C=C, m=M) == C  # a stated rating with no ratings behind it carries no weight


def test_one_rating_is_mostly_prior():
    got = car(R=5.0, v=1, C=C, m=M)
    assert got == pytest.approx((1 / 51) * 5.0 + (50 / 51) * C)
    assert C < got < C + 0.02


def test_null_rating_number_is_not_computable():
    assert car(R=4.8, v=None, C=C, m=M) is None
    assert car(R=None, v=None, C=C, m=M) is None


# --- formula behaviour -------------------------------------------------------------

def test_many_ratings_approach_item_rating():
    assert car(R=4.5, v=1_000_000, C=C, m=M) == pytest.approx(4.5, abs=1e-4)


def test_v_equal_m_is_midpoint():
    assert car(R=5.0, v=50, C=4.0, m=50) == pytest.approx(4.5)


def test_spec_example_4_9_from_46_vs_4_5_from_8431_flips_only_above_m_74():
    # SPEC §1 example. CAR always narrows the 0.40 raw gap, but whether the order flips
    # depends on m: solving for equality at C = 4.25 gives m ≈ 74.3.
    small, big = (4.9, 46), (4.5, 8431)
    assert 0 < car(*small, C, 50) - car(*big, C, 50) < 0.1  # narrowed, not flipped
    assert car(*small, C, 74) > car(*big, C, 74)
    assert car(*small, C, 75) < car(*big, C, 75)
    assert car(*small, C, 120) < car(*big, C, 120)


@pytest.mark.parametrize("m", [0, -1])
def test_nonpositive_m_rejected(m):
    with pytest.raises(ValueError):
        car(4.0, 10, C, m)


def test_negative_count_rejected():
    with pytest.raises(ValueError):
        car(4.0, -1, C, M)


def test_rating_count_without_rating_is_contradictory():
    with pytest.raises(ValueError, match="contradictory"):
        car(None, 5, C, M)


# --- priors selection: candidate set primary, fallback only under 30 -----------------

class ExplodingFallback(dict):
    def __getitem__(self, k):
        raise AssertionError("fallback must not be read for a candidate set of >= 30")


def test_candidate_set_of_30_uses_its_own_priors_and_never_reads_fallback():
    cands = [item(f"A{i}", 4.0 + (i % 2), 10 + i) for i in range(30)]
    p = priors_for(cands, ExplodingFallback())
    assert p.source == "candidate_set" and not p.flagged
    assert p.C == pytest.approx(4.5) and p.m == pytest.approx(24.5)


def test_candidate_set_of_29_falls_back_and_is_flagged():
    cands = [item(f"A{i}", 3.0, 10) for i in range(29)]
    p = priors_for(cands, {"C_simple": 4.2486, "m_median": 50.0})
    assert p.source == "fallback" and p.flagged
    assert (p.C, p.m) == (4.2486, 50.0)


def test_unrated_items_do_not_count_toward_the_floor():
    cands = [item(f"A{i}", 4.0, 10) for i in range(29)] + [item("Z", None, None)]
    assert priors_for(cands, {"C_simple": 4.0, "m_median": 50.0}).flagged


# --- ranking -----------------------------------------------------------------------

def test_rank_order_ties_and_uncomputable_last():
    cands = [
        item("B", 4.5, 100),
        item("A", 4.5, 100),   # exact tie with B -> asin order
        item("N", 5.0, None),  # not computable -> last
        item("Z", 4.9, 5),
        item("K", 4.5, 1000),
    ]
    order = [s.item.parent_asin for s in rank_by_car(cands, C=4.25, m=50)]
    assert order == ["K", "A", "B", "Z", "N"]

