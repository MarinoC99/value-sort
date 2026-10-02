"""Credibility-Adjusted Rating (SPEC.md §3).

    CAR = (v / (v + m)) · R  +  (m / (v + m)) · C

Primary path: C and m are computed over whatever candidate set the caller passes in
(C = simple mean rating, m = median rating count); no candidate matcher exists until Step 7. If the candidate set has fewer than
MIN_CANDIDATE_SET rated items, the stored fallback priors are used and the result is
flagged. See DECISIONS.md #12, #21.
"""

from __future__ import annotations

from dataclasses import dataclass

from value_sort.priors import MIN_CANDIDATE_SET, compute_priors
from value_sort.schema import Item


def car(R: float | None, v: int | None, C: float, m: float) -> float | None:
    """Return CAR, or None when rating_number is unknown (no count means no weighting).

    v = 0 is well defined: no evidence, so the item sits exactly at the prior C.
    """
    if m <= 0:
        raise ValueError(f"m must be > 0, got {m}")
    if not 1 <= C <= 5:
        raise ValueError(f"C must be in [1, 5], got {C}")
    if v is None:
        return None
    if v < 0:
        raise ValueError(f"rating_number must be >= 0, got {v}")
    if v == 0:
        return C
    if R is None:
        raise ValueError(f"rating_number={v} but average_rating is null: contradictory record")
    return (v / (v + m)) * R + (m / (v + m)) * C


@dataclass(frozen=True)
class Priors:
    C: float
    m: float
    source: str  # "candidate_set" or "fallback"
    n_rated: int  # rated items in the candidate set (what decides the source)

    @property
    def flagged(self) -> bool:
        return self.source == "fallback"


def n_rated(items: list[Item]) -> int:
    return sum(1 for i in items if i.average_rating is not None and i.rating_number)


def priors_for(candidates: list[Item], fallback: dict) -> Priors:
    """Candidate-set priors, or the stored fallback when the set is too small."""
    k = n_rated(candidates)
    if k >= MIN_CANDIDATE_SET:
        p = compute_priors(candidates)
        return Priors(C=p["C_simple"], m=p["m_median"], source="candidate_set", n_rated=k)
    return Priors(C=fallback["C_simple"], m=fallback["m_median"], source="fallback", n_rated=k)


@dataclass(frozen=True)
class Scored:
    item: Item
    car: float | None


def rank_by_car(candidates: list[Item], C: float, m: float) -> list[Scored]:
    """Descending CAR. Ties: more ratings first, then parent_asin, so order is deterministic.
    Items whose CAR is not computable (rating_number null) go last, never interleaved."""
    scored = [Scored(it, car(it.average_rating, it.rating_number, C, m)) for it in candidates]
    return sorted(
        scored,
        key=lambda s: (s.car is None, -(s.car or 0.0), -(s.item.rating_number or 0), s.item.parent_asin),
    )
