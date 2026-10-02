"""SPIKE (throwaway). INDICATIVE ONLY: not reproducible as a project result.

Title keyword matcher per DECISIONS #13: an item matches when every query word appears
in its title as a whole word, case-insensitive. Pool = priced items (DECISIONS #14).
"""

from __future__ import annotations

import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from value_sort.loader import load_items, priced  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEED = 7


def queries() -> list[str]:
    lines = (ROOT / "spike/queries.txt").read_text().splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def match(items, query: str):
    pats = [re.compile(rf"\b{re.escape(t)}\b") for t in query.lower().split()]
    return [i for i in items if all(p.search(i.title.lower()) for p in pats)]


def pool():
    raw = ROOT / "data/raw"
    items, _ = load_items(raw / "meta_Health_and_Household.slim.parquet",
                          raw / "meta_Health_and_Household.manifest.json")
    return priced(items)


if __name__ == "__main__":
    P = pool()
    print("INDICATIVE ONLY: spike output, not a project result.\n")
    for q in queries():
        s = match(P, q)
        print(f"=== {q!r}: {len(s):,} items ===")
        for i, it in enumerate(random.Random(SEED).sample(s, min(40, len(s))), 1):
            print(f"{i:>2}. {it.title[:140]}")
        print()
