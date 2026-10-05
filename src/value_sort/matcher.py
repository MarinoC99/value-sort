"""Step 7 candidate-set matcher, implementing the rules pre-registered in
config/step7_prereg.json (record: prereg/STEP7.md).

Interpretations the pre-registration does not fully specify are logged in DECISIONS.md
(55 onward) and noted inline below.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from value_sort.schema import Item

PREREG = Path("config/step7_prereg.json")
SEP = r"[\s\-]+"  # hyphen or whitespace between words (prereg: "hyphen or space")


def load_prereg(path: Path = PREREG) -> dict:
    return json.loads(path.read_text())


def _word_pattern(word: str, last: bool) -> str:
    w = re.escape(word.lower())
    if last:
        # Interpretation (DECISIONS 55): "optional plural s on the last word" means the last
        # word matches with or without one trailing s, so "baby wipes" also matches "baby wipe".
        stem = w[:-1] if w.endswith("s") else w
        return stem + "s?"
    return w


def phrase_regex(query: str) -> re.Pattern:
    words = query.lower().split()
    parts = []
    for i, w in enumerate(words):
        last = i == len(words) - 1
        if len(w) <= 2 and i > 0:
            # Short-word rule: directly after the previous word, optional digit suffix with an
            # optional hyphen ("d", "d3", "d-3"). Interpretation (DECISIONS 56): a space before
            # the digit ("d 3") does not count, and the plural rule doesn't apply to short words.
            parts.append(re.escape(w) + r"(?:-?\d+)?")
        else:
            parts.append(_word_pattern(w, last))
    return re.compile(r"(?<![a-z0-9])" + SEP.join(parts) + r"(?![a-z0-9])", re.I)


def term_regex(term: str) -> re.Pattern:
    # Exclusion terms: whole words or phrases, case-insensitive, words separated by any
    # hyphen/whitespace run. Interpretation (DECISIONS 57): applied literally, so "case" also
    # excludes "Case of 12" pack listings; the over-exclusion audit measures the cost.
    parts = [re.escape(t) for t in term.lower().split()]
    return re.compile(r"(?<![a-z0-9])" + SEP.join(parts) + r"(?![a-z0-9])", re.I)


@dataclass
class MatchResult:
    query: str
    kept: list[Item] = field(default_factory=list)
    excluded: list[tuple[Item, list[str]]] = field(default_factory=list)  # item, terms that hit


def match(items: list[Item], query: str, prereg: dict) -> MatchResult:
    m = prereg["matcher"]
    terms = list(m["exclude_all"]) + list(m["exclude_per_query"].get(query, []))
    term_res = [(t, term_regex(t)) for t in terms]
    pat = phrase_regex(query)
    res = MatchResult(query)
    for it in items:
        if not pat.search(it.title):
            continue
        hits = [t for t, r in term_res if r.search(it.title)]
        if hits:
            res.excluded.append((it, hits))
        else:
            res.kept.append(it)
    return res
