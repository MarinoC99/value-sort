"""Step 7 contamination audit sample (prereg/STEP7.md, "Contamination audit").

Per query: a seeded random sample of the kept set and of the excluded set, written to one
CSV with an empty `in_set` column for hand labelling from titles only. The file is blind:
it does not say which rows were kept or excluded, so labels can't be shaped by the matcher's
verdict. The scorer re-derives each row's group by re-running the matcher with the same rules
and seed. The file is never overwritten once any label is filled in.

Recall sample (prereg/STEP7.md, Deviation 1): titles that contain every query word as a whole
word (the spike's any-order rule, DECISIONS 13) but fail the pre-registered phrase match, written
to a second blind file in the same format. It measures what the adjacency requirement loses,
which the contamination file cannot see.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
from pathlib import Path

from value_sort.loader import load_items, priced
from value_sort.matcher import load_prereg, match, phrase_regex

OUT = Path("audit/step7_contamination.csv")
RECALL_OUT = Path("audit/step7_recall.csv")
COLUMNS = ["audit_id", "query", "parent_asin", "title", "in_set", "notes"]  # notes: added before labelling (audit/step7_README.md)


def sample_rows(pool, prereg: dict) -> list[dict]:
    a = prereg["contamination_audit"]
    seed = prereg["seed"]
    rows = []
    for q in [x["query"] for x in prereg["queries"]]:
        r = match(pool, q, prereg)
        kept = sorted(i.parent_asin for i in r.kept)
        excl = sorted(i.parent_asin for i, _ in r.excluded)
        # Interpretation (DECISIONS 58): one RNG per query, seeded "seed:query", sampling from
        # sorted IDs; where a group is smaller than its quota, all of it is taken.
        rng = random.Random(f"{seed}:{q}")
        pick = rng.sample(kept, min(a["per_query_kept_sample"], len(kept))) + \
            rng.sample(excl, min(a["per_query_excluded_sample"], len(excl)))
        rng.shuffle(pick)  # blind: kept and excluded rows interleaved
        titles = {i.parent_asin: i.title for i in r.kept} | {i.parent_asin: i.title for i, _ in r.excluded}
        rows += [{"query": q, "parent_asin": p, "title": titles[p], "in_set": "", "notes": ""} for p in pick]
    for n, row in enumerate(rows, 1):
        row["audit_id"] = n
    return rows


def any_order_regexes(query: str) -> list[re.Pattern]:
    # The spike matcher's rule, unchanged: every query word as a whole word, any order.
    return [re.compile(rf"\b{re.escape(t)}\b", re.I) for t in query.lower().split()]


def adjacency_lost(pool, query: str) -> list:
    """Titles the any-order rule matches and the phrase rule does not."""
    toks, pat = any_order_regexes(query), phrase_regex(query)
    return [i for i in pool if all(t.search(i.title) for t in toks) and not pat.search(i.title)]


def recall_rows(pool, prereg: dict) -> list[dict]:
    a = prereg["recall_audit"]
    rows = []
    for q in a["queries"]:
        lost = {i.parent_asin: i.title for i in adjacency_lost(pool, q)}
        # Same scheme as DECISIONS 58, with its own seed string so the draw is independent of
        # the contamination sample: one RNG per query, sorted IDs, whole group if under quota.
        rng = random.Random(f"{prereg['seed']}:recall:{q}")
        pick = rng.sample(sorted(lost), min(a["per_query_sample"], len(lost)))
        rows += [{"query": q, "parent_asin": p, "title": lost[p], "in_set": "", "notes": ""} for p in pick]
    for n, row in enumerate(rows, 1):
        row["audit_id"] = n
    return rows


def has_labels(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open(newline="", encoding="utf-8-sig") as f:
        return any((r.get("in_set") or "").strip() for r in csv.DictReader(f))


def write(rows: list[dict], path: Path = OUT) -> None:
    if has_labels(path):
        raise FileExistsError(f"{path} already has labels; refusing to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="Health_and_Household")
    ap.add_argument("--recall", action="store_true", help="draw the recall sample (Deviation 1) instead")
    args = ap.parse_args()
    raw = Path("data/raw")
    items, _ = load_items(raw / f"meta_{args.category}.slim.parquet", raw / f"meta_{args.category}.manifest.json")
    prereg = load_prereg()
    rows, out = (recall_rows(priced(items), prereg), RECALL_OUT) if args.recall else \
        (sample_rows(priced(items), prereg), OUT)
    write(rows, out)
    per = {}
    for r in rows:
        per[r["query"]] = per.get(r["query"], 0) + 1
    print(f"Wrote {len(rows)} rows to {out}; in_set empty. Per query: {per}")


if __name__ == "__main__":
    main()
