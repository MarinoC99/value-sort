"""Score the pack-size extractor against the hand labels in audit/unit_price_labels.csv.

Refuses to score a partially labelled file. Rules are in audit/README.md and fixed before
labelling (DECISIONS.md #31). The threshold comes from config/unit_price.json.

Also reports extractor coverage over the whole priced pool, which needs no labels.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from value_sort.loader import load_items, priced
from value_sort.unit_price import TO_BASE, Extraction, extract, load_threshold, _unit
from value_sort.unit_price_audit import AUDIT_CSV

GUARDRAIL = 0.90
QTY_TOL = 0.01
_TRUTH = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(fl oz|oz|lb|g|kg|ml|l|gal|qt|pt|ct)\s*$", re.I)


class LabelError(ValueError):
    pass


@dataclass(frozen=True)
class Truth:
    kind: str  # "size", "none", "na"
    count: float = 0.0
    size: float = 0.0
    unit: str = ""

    @property
    def dimension(self) -> str:
        return TO_BASE[self.unit][0]

    @property
    def total(self) -> float:
        return self.count * self.size * TO_BASE[self.unit][1]


def parse_truth(s: str) -> Truth:
    v = s.strip()
    if v.upper() == "NONE":
        return Truth("none")
    if v.upper() == "N/A":
        return Truth("na")
    m = _TRUTH.match(v)
    if not m:
        raise LabelError(f"can't parse truth {s!r}; expected 'COUNT x SIZE UNIT', NONE, or N/A")
    unit = "ct" if m.group(3).lower() == "ct" else _unit(m.group(3))
    return Truth("size", float(m.group(1)), float(m.group(2)), unit)


def judge(e: Extraction, t: Truth) -> str:
    """One of: correct, wrong, abstained."""
    r = e.result
    if r is None:
        return "abstained"
    if t.kind == "none":
        return "wrong"
    if t.kind == "na":
        return "correct" if r.dimension == "count" and abs(r.total_base - 1) < 1e-9 else "wrong"
    ok = r.dimension == t.dimension and abs(r.total_base - t.total) <= QTY_TOL * t.total
    return "correct" if ok else "wrong"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def read_labels(path: Path) -> list[dict]:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))
    empty = [r["audit_id"] for r in rows if not (r.get("truth") or "").strip()]
    if empty:
        raise LabelError(f"{len(empty)} of {len(rows)} rows have no truth label (e.g. audit_id {empty[:5]}); "
                         "refusing to score a partial audit")
    return rows


def score(rows: list[dict], items_by_id: dict, threshold: float) -> dict:
    results = []
    for r in rows:
        t = parse_truth(r["truth"])
        e = extract(items_by_id[r["parent_asin"]], threshold)
        v = judge(e, t)
        exact = (e.result is not None and t.kind == "size" and v == "correct"
                 and abs(e.result.count - t.count) < 1e-9
                 and abs(e.result.size * TO_BASE[e.result.unit][1] - t.size * TO_BASE[t.unit][1]) <= QTY_TOL * t.size * TO_BASE[t.unit][1])
        results.append({"audit_id": r["audit_id"], "parent_asin": r["parent_asin"], "title": r["title"],
                        "truth": r["truth"], "truth_kind": t.kind, "verdict": v, "exact": exact,
                        "extracted": None if e.result is None else f"{e.result.count:g} x {e.result.size:g} {e.result.unit}",
                        "confidence": e.confidence, "flag": e.flag})

    def prec(rs):
        ret = [x for x in rs if x["verdict"] != "abstained"]
        k = sum(x["verdict"] == "correct" for x in ret)
        lo, hi = wilson(k, len(ret))
        return {"returned": len(ret), "correct": k,
                "precision": k / len(ret) if ret else None, "ci95": [lo, hi]}

    kinds = Counter(x["truth_kind"] for x in results)
    all_p = prec(results)
    no_na = prec([x for x in results if x["truth_kind"] != "na"])
    ret = [x for x in results if x["verdict"] != "abstained"]
    return {
        "threshold": threshold,
        "n_labelled": len(results),
        "truth_kinds": dict(kinds),
        "coverage": len(ret) / len(results),
        "precision_all": all_p,
        "precision_excluding_na": no_na,
        "exact_count_and_size_match": sum(x["exact"] for x in ret),
        "labelled_but_abstained": sum(1 for x in results if x["truth_kind"] == "size" and x["verdict"] == "abstained"),
        "returned_where_truth_none": sum(1 for x in results if x["truth_kind"] == "none" and x["verdict"] == "wrong"),
        "guardrail": GUARDRAIL,
        "passes_guardrail": (all_p["precision"] or 0) >= GUARDRAIL,
        "errors": [x for x in results if x["verdict"] == "wrong"],
        "rows": results,
    }


def pool_coverage(pool: list, threshold: float) -> dict:
    flags, dims, n = Counter(), Counter(), 0
    for it in pool:
        e = extract(it, threshold)
        if e.result:
            n += 1
            dims[e.result.dimension] += 1
        else:
            flags[e.flag] += 1
    return {"n_items": len(pool), "extracted": n, "coverage": n / len(pool),
            "by_dimension": dict(dims), "abstain_reasons": dict(flags.most_common())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="Health_and_Household")
    ap.add_argument("--coverage-only", action="store_true", help="skip label scoring")
    args = ap.parse_args()
    threshold = load_threshold()
    raw = Path("data/raw")
    items, _ = load_items(raw / f"meta_{args.category}.slim.parquet", raw / f"meta_{args.category}.manifest.json")
    pool = priced(items)

    cov = pool_coverage(pool, threshold)
    Path(f"reports/unit_price_coverage_{args.category}.json").write_text(json.dumps(cov, indent=2))
    print(f"Pool coverage at threshold {threshold}: {cov['extracted']:,} / {cov['n_items']:,} "
          f"({100 * cov['coverage']:.1f}%) priced items get a pack size; by dimension {cov['by_dimension']}")
    print("Abstain reasons:", cov["abstain_reasons"])
    if args.coverage_only:
        return

    rows = read_labels(AUDIT_CSV)
    res = score(rows, {i.parent_asin: i for i in pool}, threshold)
    Path("reports/unit_price_precision.json").write_text(json.dumps(res, indent=2))
    p, q = res["precision_all"], res["precision_excluding_na"]
    fmt = lambda x: "n/a" if x["precision"] is None else f"{100 * x['precision']:.1f}% ({x['correct']}/{x['returned']}), 95% CI {100 * x['ci95'][0]:.1f}–{100 * x['ci95'][1]:.1f}%"
    print(f"\nLabelled: {res['n_labelled']}  truth kinds: {res['truth_kinds']}")
    print(f"Coverage on audit set:     {100 * res['coverage']:.1f}%")
    print(f"PRECISION (all):           {fmt(p)}")
    print(f"Precision (excluding N/A): {fmt(q)}")
    print(f"Exact count and size:      {res['exact_count_and_size_match']} of {p['returned']}")
    print(f"Guardrail >= {GUARDRAIL:.0%}:          {'PASS' if res['passes_guardrail'] else 'FAIL: SPEC kill criterion 3 (drop the NUP module)'}")
    for x in res["errors"]:
        print(f"  WRONG #{x['audit_id']}: extracted {x['extracted']} vs truth {x['truth']} | {x['title'][:80]}")


if __name__ == "__main__":
    main()
