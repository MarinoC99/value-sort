"""SPIKE task 4, follow-up checks. INDICATIVE ONLY: not reproducible as a project result.

These two checks were first run as ad-hoc commands during the spike and their output was
added to out/task4.json outside task4.py. This script is those commands, committed afterwards so
the sections are reproducible. Run it after task4.py (which rewrites task4.json without
them). With --check it recomputes and compares against the committed file, writing nothing.

  car_vs_car_across_m  How much CAR's own top 20 (at the set's m) changes at other m.
  car_vs_popularity    Whether CAR's top 20 is just the most-reviewed items: top-20 overlap
                       with a rating-count sort, and Spearman of CAR against rating count
                       and against star rating across the whole set.
"""

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from matcher import match, pool  # noqa: E402
from value_sort.car import priors_for, rank_by_car  # noqa: E402
from value_sort.priors import load_fallback  # noqa: E402

QUERIES = ["protein powder", "hand sanitizer", "toilet paper", "blood pressure monitor"]


def car_vs_car(c, p) -> dict:
    t = lambda m: [s.item.parent_asin for s in rank_by_car(c, p.C, m)[:20]]  # noqa: E731
    base = set(t(p.m))
    return {"set_m": p.m, **{f"car_top20_overlap_set_m_vs_{m}": len(base & set(t(m))) for m in (25, 50, 120, 500)}}


def car_vs_popularity(c, p) -> dict:
    ranked = rank_by_car(c, p.C, p.m)
    car = [s.item for s in ranked]
    pop = sorted(c, key=lambda i: (-i.rating_number, i.parent_asin))
    ct, pt = car[:20], pop[:20]
    d = pd.DataFrame({"car": [s.car for s in ranked], "n": [i.rating_number for i in car],
                      "r": [i.average_rating for i in car]})
    return {
        "car_top20_overlap_with_most_reviewed_top20": len({i.parent_asin for i in ct} & {i.parent_asin for i in pt}),
        "car_top20_min_rating": min(i.average_rating for i in ct),
        "most_reviewed_top20_min_rating": min(i.average_rating for i in pt),
        "most_reviewed_top20_ratings": sorted({i.average_rating for i in pt}),
        # Spearman as Pearson on ranks (no scipy dependency)
        "spearman_car_vs_rating_count_whole_set": round(d.car.rank().corr(d.n.rank()), 3),
        "spearman_car_vs_avg_rating_whole_set": round(d.car.rank().corr(d.r.rank()), 3),
    }


def main() -> None:
    P, fb = pool(), load_fallback("Health_and_Household")
    sets = {q: match(P, q) for q in QUERIES}
    pri = {q: priors_for(c, fb) for q, c in sets.items()}
    new = {
        "car_vs_car_across_m": {q: car_vs_car(sets[q], pri[q]) for q in QUERIES},
        "car_vs_popularity": {q: car_vs_popularity(sets[q], pri[q]) for q in QUERIES},
    }
    path = HERE / "out/task4.json"
    d = json.loads(path.read_text())
    if "--check" in sys.argv:
        same = all(json.loads(json.dumps(new[k])) == d.get(k) for k in new)
        print("INDICATIVE ONLY. Matches committed task4.json:", same)
        sys.exit(0 if same else 1)
    d.update(new)
    path.write_text(json.dumps(d, indent=1))
    print("INDICATIVE ONLY: wrote car_vs_car_across_m and car_vs_popularity to out/task4.json")


if __name__ == "__main__":
    main()
