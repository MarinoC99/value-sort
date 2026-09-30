"""Profile the slim metadata file before any modeling.

Writes reports/profile_<category>.json (machine-readable; Step 4 reads m and C from it)
and reports/profile_<category>.md (for humans).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

PERCENTILES = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]


def parse_raw(series: pd.Series) -> pd.Series:
    return series.map(json.loads)


def numeric_or_nan(values: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Split raw values into numeric (float) and the non-null, non-numeric leftovers."""
    is_num = values.map(lambda v: isinstance(v, (int, float)) and not isinstance(v, bool))
    num = values.where(is_num).astype("float64")
    other = values[~is_num & values.notna()]
    return num, other


def profile(path: Path) -> dict:
    df = pd.read_parquet(path)
    n = len(df)

    price_raw = parse_raw(df["price"])
    price, price_other = numeric_or_nan(price_raw)
    rating_raw = parse_raw(df["average_rating"])
    rating, rating_other = numeric_or_nan(rating_raw)
    count_raw = parse_raw(df["rating_number"])
    count, count_other = numeric_or_nan(count_raw)

    rated = rating.notna() & count.notna() & (count >= 1)
    pos_price = price[price > 0]

    return {
        "source_file": str(path),
        "rows": n,
        "duplicate_parent_asin": int(df["parent_asin"].duplicated().sum()),
        "price": {
            "pct_non_null": round(100 * price_raw.notna().mean(), 2),
            "pct_numeric": round(100 * price.notna().mean(), 2),
            "non_null_non_numeric_count": int(len(price_other)),
            "non_numeric_examples": price_other.astype(str).value_counts().head(10).to_dict(),
            "zero_or_negative_count": int((price <= 0).sum()),
            "distribution_usd": {
                "n": int(pos_price.size),
                "mean": round(float(pos_price.mean()), 2),
                "min": float(pos_price.min()),
                **{f"p{int(q * 100)}": round(float(pos_price.quantile(q)), 2) for q in PERCENTILES},
                "max": float(pos_price.max()),
            },
            "histogram_usd": (
                pd.cut(pos_price, [0, 5, 10, 15, 20, 30, 50, 100, 200, 500, float("inf")], right=False)
                .value_counts(sort=False).rename(str).to_dict()
            ),
        },
        "average_rating": {
            "pct_non_null": round(100 * rating_raw.notna().mean(), 2),
            "non_null_non_numeric_count": int(len(rating_other)),
            "out_of_range_count": int(((rating < 1) | (rating > 5)).sum()),
        },
        "rating_number": {
            "pct_non_null": round(100 * count_raw.notna().mean(), 2),
            "non_null_non_numeric_count": int(len(count_other)),
            "zero_count": int((count == 0).sum()),
            "pct_ge_1": round(100 * (count >= 1).mean(), 2),
        },
        "car_priors": {
            "population": "items with numeric average_rating and rating_number >= 1",
            "n_items": int(rated.sum()),
            "C_mean_rating_unweighted": round(float(rating[rated].mean()), 4),
            "m_median_rating_count": float(count[rated].median()),
            "reference_only": {
                "C_mean_rating_weighted_by_count": round(
                    float((rating[rated] * count[rated]).sum() / count[rated].sum()), 4
                ),
                "rating_count_percentiles": {
                    f"p{int(q * 100)}": float(count[rated].quantile(q)) for q in PERCENTILES
                },
            },
        },
    }


def to_markdown(p: dict, category: str) -> str:
    pr, rn, car = p["price"], p["rating_number"], p["car_priors"]
    d = pr["distribution_usd"]
    lines = [
        f"# Profile: {category}",
        "",
        f"Source: `{p['source_file']}` (slim Parquet streamed from Amazon Reviews 2023).",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Rows (items) | {p['rows']:,} |",
        f"| Duplicate parent_asin | {p['duplicate_parent_asin']:,} |",
        f"| % items with non-null price | {pr['pct_non_null']}% |",
        f"| % items with numeric price | {pr['pct_numeric']}% |",
        f"| % items with non-null rating_number | {rn['pct_non_null']}% |",
        f"| % items with rating_number >= 1 | {rn['pct_ge_1']}% |",
        f"| Category mean rating, C (unweighted, rated items) | {car['C_mean_rating_unweighted']} |",
        f"| Median rating count, m (rated items) | {car['m_median_rating_count']:g} |",
        f"| Items in C/m population | {car['n_items']:,} |",
        "",
        "## Price distribution (USD, price > 0)",
        "",
        "| n | mean | p1 | p5 | p10 | p25 | p50 | p75 | p90 | p95 | p99 | max |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
        "| " + " | ".join(
            [f"{d['n']:,}", f"{d['mean']}"]
            + [f"{d[k]}" for k in ["p1", "p5", "p10", "p25", "p50", "p75", "p90", "p95", "p99"]]
            + [f"{d['max']:,}"]
        ) + " |",
        "",
        "| Bucket | Items |",
        "|---|---|",
        *[f"| {k} | {v:,} |" for k, v in pr["histogram_usd"].items()],
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="Health_and_Household")
    args = ap.parse_args()
    src = Path("data/raw") / f"meta_{args.category}.slim.parquet"
    p = profile(src)
    out = Path("reports")
    out.mkdir(exist_ok=True)
    (out / f"profile_{args.category}.json").write_text(json.dumps(p, indent=2))
    md = to_markdown(p, args.category)
    (out / f"profile_{args.category}.md").write_text(md)
    print(md)
    print(json.dumps({k: p[k] for k in ["price", "average_rating", "rating_number", "car_priors"]}, indent=2))


if __name__ == "__main__":
    main()
