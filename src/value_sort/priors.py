"""CAR priors (C, m) over a set of items.

Primary path (Step 4): priors are computed over each candidate set at rank time.
Fallback only: when a candidate set has fewer than MIN_CANDIDATE_SET items, the global
priced-set priors stored in reports/priors_fallback_<Category>.json are used instead and
the result is flagged. The fallback file is never the default. See DECISIONS.md #12, #21.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from value_sort.loader import load_items, priced
from value_sort.schema import Item

MIN_CANDIDATE_SET = 30
FALLBACK_ROLE = f"fallback_only_when_candidate_set_lt_{MIN_CANDIDATE_SET}"


def compute_priors(items: list[Item]) -> dict:
    rated = [i for i in items if i.average_rating is not None and i.rating_number]
    if not rated:
        raise ValueError("no rated items to compute priors from")
    r = [i.average_rating for i in rated]
    n = [i.rating_number for i in rated]
    return {
        "n_items": len(rated),
        "C_simple": statistics.fmean(r),
        "C_weighted": sum(a * b for a, b in zip(r, n)) / sum(n),
        "m_median": float(statistics.median(n)),
    }


def fallback_path(category: str) -> Path:
    return Path("reports") / f"priors_fallback_{category}.json"


def load_fallback(category: str) -> dict:
    data = json.loads(fallback_path(category).read_text())
    if data.get("role") != FALLBACK_ROLE:
        raise ValueError(f"{fallback_path(category)} is not a fallback priors file")
    return data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="Health_and_Household")
    args = ap.parse_args()
    raw = Path("data/raw")
    items, _ = load_items(raw / f"meta_{args.category}.slim.parquet", raw / f"meta_{args.category}.manifest.json")
    out = {
        "role": FALLBACK_ROLE,
        "use": (
            f"Only when a candidate set has fewer than {MIN_CANDIDATE_SET} items; the result must be "
            "flagged. The primary path computes C and m over the candidate set at rank time."
        ),
        "population": "all loaded items with a valid price > 0 (loader.priced)",
        "min_candidate_set": MIN_CANDIDATE_SET,
        **compute_priors(priced(items)),
    }
    fallback_path(args.category).write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
