"""CAR sensitivity harness: how does the top-K move as C and m change?

Scope (DECISIONS.md #22, #23): no candidate matcher exists until Step 7, so this runs over
the whole priced pool, with C in {priced-set simple mean, priced-set count-weighted mean}
and m from config. Those C values are analysis inputs here, not a ranking default.
Candidate-set-mean C sensitivity is deferred to Step 7.

There is no privileged baseline: every combination is compared with every other, and each
is also compared with a raw average_rating sort (what CAR changes at all).

m values, C sources and K come from config/car_sensitivity.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from value_sort.car import rank_by_car
from value_sort.loader import load_items, priced
from value_sort.priors import load_fallback

C_LABEL = {"C_simple": "simple", "C_weighted": "count-weighted"}


def overlap(a: list[str], b: list[str]) -> int:
    return len(set(a) & set(b))


def run(category: str, config: dict) -> dict:
    raw = Path("data/raw")
    items, _ = load_items(raw / f"meta_{category}.slim.parquet", raw / f"meta_{category}.manifest.json")
    pool = priced(items)
    priors = load_fallback(category)  # priced-set values; used here as analysis inputs only
    k = config["top_k"]

    combos = []
    for c_key in config["C_sources"]:
        for m in config["m_values"]:
            ranked = rank_by_car(pool, priors[c_key], m)
            cars = [s.car for s in ranked]
            combos.append({
                "id": f"{C_LABEL[c_key]} C, m={m}",
                "C_source": c_key, "C": priors[c_key], "m": m,
                # rounded to 1e-9 so float noise can't manufacture distinct values
                "distinct_car": len({round(c, 9) for c in cars}),
                "distinct_car_at_2dp": len({round(c, 2) for c in cars}),
                "top": [
                    {"parent_asin": s.item.parent_asin, "title": s.item.title,
                     "average_rating": s.item.average_rating, "rating_number": s.item.rating_number,
                     "car": s.car}
                    for s in ranked[:k]
                ],
            })

    raw_top = sorted(pool, key=lambda i: (-i.average_rating, -i.rating_number, i.parent_asin))[:k]
    raw_ids = [i.parent_asin for i in raw_top]
    ids = {c["id"]: [t["parent_asin"] for t in c["top"]] for c in combos}

    return {
        "distinct_star_ratings": len({i.average_rating for i in pool}),
        "distinct_rating_and_count_pairs": len({(i.average_rating, i.rating_number) for i in pool}),
        "category": category,
        "population": "all priced items (loader.priced)",
        "n_items": len(pool),
        "top_k": k,
        "m_values": config["m_values"],
        "C_values": {C_LABEL[c]: priors[c] for c in config["C_sources"]},
        "combos": combos,
        "pairwise_overlap": {a: {b: overlap(ids[a], ids[b]) for b in ids} for a in ids},
        "raw_rating_sort": {
            "overlap_with_each_combo": {a: overlap(ids[a], raw_ids) for a in ids},
            "median_rating_number_in_top": sorted(i.rating_number for i in raw_top)[k // 2],
            "top": [{"parent_asin": i.parent_asin, "average_rating": i.average_rating,
                     "rating_number": i.rating_number} for i in raw_top],
        },
    }


def to_markdown(r: dict) -> str:
    k, combos = r["top_k"], r["combos"]
    names = [c["id"] for c in combos]
    L = [
        f"# CAR sensitivity: {r['category']}",
        "",
        f"Population: {r['population']}, n = {r['n_items']:,}. Top {k} by CAR under each (C, m).",
        "C values: " + ", ".join(f"{n} = {v:.4f}" for n, v in r["C_values"].items()) + ".",
        "",
        "Scope: whole priced pool, because no candidate matcher exists until Step 7. "
        "Candidate-set-mean C sensitivity is deferred to Step 7 (DECISIONS.md #22).",
        "",
        f"## Top-{k} overlap between every pair of settings",
        "",
        "| | " + " | ".join(names) + " |",
        "|---|" + "---|" * len(names),
    ]
    for a in names:
        L.append(f"| **{a}** | " + " | ".join(
            "—" if a == b else f"{r['pairwise_overlap'][a][b]}" for b in names) + " |")

    raw = r["raw_rating_sort"]
    L += [
        "",
        f"## Compared with a raw average_rating sort",
        "",
        f"Median rating_number in the raw-sort top {k}: {raw['median_rating_number_in_top']:,}.",
        "",
        "| Setting | Overlap with raw-sort top " + str(k) + " |",
        "|---|---|",
        *[f"| {a} | {raw['overlap_with_each_combo'][a]} / {k} |" for a in names],
        "",
        "## Distinct values: CAR vs the star rating in the data (recorded to one decimal)",
        "",
        f"Distinct star ratings: {r['distinct_star_ratings']}. Distinct (rating, rating count) pairs: "
        f"{r['distinct_rating_and_count_pairs']:,}. CAR depends only on those two fields, so that is its "
        "upper bound. Values are compared at 1e-9 so float noise cannot add distinct values; the 2 dp "
        "column is what a two-decimal display would show.",
        "",
        "| Setting | Distinct CAR | Distinct CAR at 2 dp |",
        "|---|---|---|",
        *[f"| {c['id']} | {c['distinct_car']:,} | {c['distinct_car_at_2dp']:,} |" for c in combos],
        "",
        f"## Rank of every item that reaches the top {k} under any setting",
        "",
        "Blank = outside the top " + str(k) + ".",
        "",
        "| parent_asin | title | rating | ratings | " + " | ".join(names) + " |",
        "|---|---|---|---|" + "---|" * len(names),
    ]
    rank = {c["id"]: {t["parent_asin"]: i + 1 for i, t in enumerate(c["top"])} for c in combos}
    info = {t["parent_asin"]: t for c in combos for t in c["top"]}
    order = sorted(info, key=lambda a: min(rank[n].get(a, 999) for n in names) * 100
                   + sum(rank[n].get(a, 99) for n in names) / 100)
    for a in order:
        t = info[a]
        title = t["title"].replace("|", "/")
        title = title[:55] + ("…" if len(title) > 55 else "")
        L.append(f"| {a} | {title} | {t['average_rating']} | {t['rating_number']:,} | "
                 + " | ".join(str(rank[n].get(a, "")) for n in names) + " |")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="Health_and_Household")
    ap.add_argument("--config", type=Path, default=Path("config/car_sensitivity.json"))
    args = ap.parse_args()
    r = run(args.category, json.loads(args.config.read_text()))
    Path(f"reports/car_sensitivity_{args.category}.json").write_text(json.dumps(r, indent=2))
    md = to_markdown(r)
    Path(f"reports/car_sensitivity_{args.category}.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
