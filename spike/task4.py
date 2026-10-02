"""SPIKE task 4. INDICATIVE ONLY: not reproducible as a project result.

Does CAR do anything per query? For each candidate set: the set's own priors (DECISIONS #12),
and top-20 overlap between a CAR sort and a plain average_rating sort. Same raw-sort
tie-break as the Step 4 sweep (rating desc, rating count desc, parent_asin).
"""

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from matcher import match, pool  # noqa: E402
from value_sort.car import priors_for, rank_by_car  # noqa: E402
from value_sort.priors import load_fallback  # noqa: E402

PRIMARY = ["protein powder", "hand sanitizer"]
SUPPLEMENTARY = ["toilet paper", "blood pressure monitor"]  # not requested; CAR is unaffected by their unit-price issues
SWEEP = [25, 50, 120, 500]
K = 20


def top(items, k=K):
    return [i.parent_asin for i in items[:k]]


def raw_sort(cands):
    return sorted(cands, key=lambda i: (-i.average_rating, -i.rating_number, i.parent_asin))


def row(q, P, fb):
    cands = match(P, q)
    pri = priors_for(cands, fb)
    raw = raw_sort(cands)
    car_sorted = [s.item for s in rank_by_car(cands, pri.C, pri.m)]
    raw_ids, car_ids = top(raw), top(car_sorted)
    sweep = {m: len(set(top([s.item for s in rank_by_car(cands, pri.C, m)])) & set(raw_ids)) for m in SWEEP}
    return {
        "query": q, "set_size": len(cands), "C": pri.C, "m": pri.m, "source": pri.source,
        "flagged_under_30": pri.flagged,
        "overlap_car_vs_raw_top20": len(set(raw_ids) & set(car_ids)),
        "median_ratings_raw_top20": statistics.median(i.rating_number for i in raw[:K]),
        "median_ratings_car_top20": statistics.median(i.rating_number for i in car_sorted[:K]),
        "raw_top20_ratings_of_5.0": sum(i.average_rating == 5.0 for i in raw[:K]),
        "overlap_at_m_sweep (set C)": sweep,
    }


if __name__ == "__main__":
    P, fb = pool(), load_fallback("Health_and_Household")
    out = {"_note": "SPIKE. INDICATIVE ONLY.", "primary": [row(q, P, fb) for q in PRIMARY],
           "supplementary": [row(q, P, fb) for q in SUPPLEMENTARY]}
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out/task4.json").write_text(json.dumps(out, indent=1))
    print("INDICATIVE ONLY: spike output, not a project result.")
    print(json.dumps(out, indent=1))
