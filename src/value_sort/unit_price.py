"""Pack-size extraction for Normalized Unit Price (SPEC §3).

Reads the title plus EXTRACTOR_DETAIL_KEYS only. Never guesses: every source produces
*readings* (dimension + total quantity), readings are grouped by agreement, and a result is
returned only if its confidence clears the threshold. Otherwise the result is None with a
flag reason, and the item keeps its listed price (fails open).

Confidence levels (fixed before scoring; threshold lives in config/unit_price.json):
  0.95  title agrees with at least one strong details source
  0.85  two strong details sources agree, title silent
  0.80  title alone, one unambiguous reading, nothing contradicts
  0.75  one strong details source alone (Size with a unit, Unit Count != 1, a volume field)
  0.60  title alone but size-vs-count is ambiguous (e.g. "2.1 oz, 10 count")
  0.30  any strong source contradicts the chosen reading

`Item Weight` is deliberately unused: in development data it often holds shipping or
placeholder weight. `Number of Items` / `Item Package Quantity` only corroborate, since
they mean pack count on some listings and piece count on others.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

from value_sort.schema import Item

AGREE_TOL = 0.02  # readings within 2% are the same quantity
MULTIPLIER_MAX = 24  # "N pack" with N <= 24 is a multiplier; above, it is a piece count

TO_BASE = {  # unit -> (dimension, factor to base unit: g, ml, ct)
    "oz": ("weight", 28.349523125), "lb": ("weight", 453.59237), "g": ("weight", 1.0),
    "kg": ("weight", 1000.0),
    "fl oz": ("volume", 29.5735295625), "ml": ("volume", 1.0), "l": ("volume", 1000.0),
    "gal": ("volume", 3785.411784), "qt": ("volume", 946.352946), "pt": ("volume", 473.176473),
    "ct": ("count", 1.0),
}

_UNIT_ALIASES = [
    (r"fl\.?\s*oz\.?|fluid\s*ounces?|fl\.\s*ounces?", "fl oz"),
    (r"ounces?|oz\.?", "oz"),
    (r"pounds?|lbs?\.?", "lb"),
    (r"kilograms?|kgs?", "kg"),
    (r"grams?|gr|g", "g"),
    (r"milliliters?|millilitres?|ml", "ml"),
    (r"liters?|litres?|ltr|l", "l"),
    (r"gallons?|gal", "gal"),
    (r"quarts?|qt", "qt"),
    (r"pints?|pt", "pt"),
]
_UNIT_RE = "|".join(f"(?:{p})" for p, _ in _UNIT_ALIASES)

_COUNT_NOUNS = (
    r"count|ct|capsules?|caps|vcaps|veg(?:gie)?\s*caps(?:ules)?|tablets?|tabs|caplets?|softgels?|"
    r"soft\s*gels|gummies|gummy|pieces|pcs|pc|bags|wipes|sheets|pods|packets|sachets|sticks|"
    r"lozenges|rolls|towelettes|pads|liners|napkins|cups|plates|bars|chews|lollipops|patches|"
    r"strips|swabs|tampons|diapers|pairs|refills|cartridges|filters|batteries|ea|each"
)
_NUM = r"(\d+(?:\.\d+)?|\d+/\d+)"

_SIZE = re.compile(rf"(?<![\w.]){_NUM}\s*-?\s*({_UNIT_RE})(?![a-z])")
_COUNT = re.compile(rf"(?<![\w.])(\d+)\s*-?\s*(?:{_COUNT_NOUNS})(?![a-z])")
_COUNT_APOS = re.compile(r"(?<![\w.])(\d+)'s\b|(?<![\w.])(\d{2,})s\b")  # "60's", "96s"
_N_X_SIZE = re.compile(rf"(?<![\w.])(\d+)\s*x\s*{_NUM}\s*-?\s*({_UNIT_RE})(?![a-z])")
_N_X_COUNT = re.compile(rf"(?<![\w.])(\d+)\s*x\s*(\d+)\s*-?\s*(?:{_COUNT_NOUNS}|pack|pk)(?![a-z])")
_PACKS_OF = re.compile(r"(?<![\w.])(\d+)\s*-?\s*(?:packs?|boxes|bottles|tubes|cans|jars|bags)\s+of\s+(\d+)\b")
_MULT_OF = re.compile(r"\b(?:pack|set|case|bundle|lot)\s+of\s+(\d+)\b")
_N_PACK = re.compile(r"(?<![\w.])(\d+)\s*-?\s*(?:pack|pk|packs|count\s+pack)(?![a-z])")
_PER_CONTAINER = re.compile(r"(?<![\w.])(\d+)\s*/\s*(?:bag|box|pack|case|bottle|roll)\b|\b(?:box|bag|tub|jar|bottle)\s+of\s+(\d+)\b")
_KIT = re.compile(r"\b(?:kit|includes)\b")
_CAPACITY = re.compile(
    r"\b(?:cups?|glass(?:es)?|containers?|tumblers?|mugs?|bowls?|plates?|lids?|liners?|trash\s+bags?|"
    r"garbage\s+bags?|can\s+liners?|buckets?|pitchers?|flasks?|shaker|dispensers?|spray\s+bottles?|"
    r"empty|reusable\s+bottles?|water\s+bottles?|sleeves?)\b"
)


_NUTRITION = re.compile(
    rf"(?<![\w.]){_NUM}\s*g\s+(?:of\s+)?(?:protein|sugars?|fiber|fibre|carbs?|net\s+carbs|fat|collagen|creatine)\b"
)


def _num(s: str) -> float:
    return float(Fraction(s)) if "/" in s else float(s)


def _unit(raw: str) -> str:
    raw = raw.strip().lower()
    for pat, canon in _UNIT_ALIASES:
        if re.fullmatch(pat, raw):
            return canon
    raise ValueError(f"unknown unit {raw!r}")


@dataclass(frozen=True)
class Reading:
    dimension: str
    count: float  # number of packages
    size: float  # amount per package, in `unit`
    unit: str
    source: str
    strong: bool = True

    @property
    def total(self) -> float:
        return self.count * self.size * TO_BASE[self.unit][1]


@dataclass(frozen=True)
class PackSize:
    count: float
    size: float
    unit: str
    dimension: str
    total_base: float  # grams, millilitres, or count
    confidence: float
    sources: tuple[str, ...]


@dataclass(frozen=True)
class Extraction:
    result: PackSize | None
    confidence: float
    flag: str | None  # reason when result is None
    readings: tuple[Reading, ...] = field(default=())


def _agree(a: float, b: float) -> bool:
    return abs(a - b) <= AGREE_TOL * max(a, b)


def _reconcile(values: list[float], mult: float | None) -> float | None | str:
    """Collapse repeated mentions. Returns the per-package value, None, or 'conflict'."""
    if not values:
        return None
    uniq: list[float] = []
    for v in sorted(values):
        if not any(_agree(v, u) for u in uniq):
            uniq.append(v)
    if len(uniq) == 1:
        return values[0]  # all mentions agree: keep the first, as written
    if len(uniq) == 2 and mult and _agree(uniq[1], uniq[0] * mult):
        return uniq[0]  # the larger mention is the pack total
    return "conflict"


def _norm(title: str) -> str:
    t = title.lower().replace("×", " x ").replace("*", " x ")
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)  # 1,200 -> 1200
    return _NUTRITION.sub(" ", t)  # "25g protein" is nutrition, not package size


def title_multiplier(title: str) -> float | None:
    """A lone pack multiplier ("Pack of 4", "6 Pack"), used to cross-check details counts."""
    t = _norm(title)
    ms = [float(x) for x in _MULT_OF.findall(t)] + [float(x) for x in _N_PACK.findall(t) if float(x) <= MULTIPLIER_MAX]
    return ms[0] if len(set(ms)) == 1 and ms[0] > 1 else None


def parse_title(title: str) -> tuple[list[Reading], str | None]:
    """Readings from the title, plus an ambiguity flag."""
    t = _norm(title)

    for m in _N_X_SIZE.finditer(t):
        u = _unit(m.group(3))
        if not _CAPACITY.search(t):
            return [Reading(TO_BASE[u][0], float(m.group(1)), _num(m.group(2)), u, "title")], None
    for m in _N_X_COUNT.finditer(t):
        return [Reading("count", float(m.group(1)), float(m.group(2)), "ct", "title")], None
    for m in _PACKS_OF.finditer(t):
        return [Reading("count", float(m.group(1)), float(m.group(2)), "ct", "title")], None

    mults = [float(x) for x in _MULT_OF.findall(t)]
    counts = [float(x) for x in _COUNT.findall(t)] + [float(a or b) for a, b in _COUNT_APOS.findall(t)]
    for g1, g2 in _PER_CONTAINER.findall(t):
        counts.append(float(g1 or g2))
    for n in (float(x) for x in _N_PACK.findall(t)):
        (mults if n <= MULTIPLIER_MAX else counts).append(n)

    mult_vals = {m for m in mults}
    if len(mult_vals) > 1:
        return [], "title_conflicting_pack_counts"
    mult = mults[0] if mults else None

    by_dim: dict[str, list[tuple[float, str]]] = {"weight": [], "volume": []}
    if not _CAPACITY.search(t):
        for n, u in _SIZE.findall(t):
            unit = _unit(u)
            by_dim[TO_BASE[unit][0]].append((_num(n), unit))

    sizes = {}
    for dim, found in by_dim.items():
        if not found:
            continue
        unit = found[0][1]
        in_unit = [v * TO_BASE[u][1] / TO_BASE[unit][1] for v, u in found]
        r = _reconcile(in_unit, mult)
        if r == "conflict":
            return [], f"title_conflicting_{dim}"
        sizes[dim] = (r, unit)

    c = _reconcile(counts, mult)
    if c == "conflict":
        return [], "title_conflicting_counts"

    pack = mult or 1.0
    if sizes and c is not None:
        # "2.1 oz, 10 count": the count is probably packages of that size, but not certainly.
        dim, (s, unit) = next(iter(sizes.items()))
        return [Reading(dim, c * pack, s, unit, "title")], "title_size_count_ambiguous"
    if len(sizes) == 2:
        return [Reading(d, pack, s, u, "title") for d, (s, u) in sizes.items()], "title_weight_and_volume"
    if sizes:
        dim, (s, unit) = next(iter(sizes.items()))
        return [Reading(dim, pack, s, unit, "title")], None
    if c is not None:
        return [Reading("count", pack, c, "ct", "title")], None
    return [], None


# Amazon's standard Size / Unit Count format: number, space, full unit word.
_CANONICAL = re.compile(
    r"^\s*\d+(?:\.\d+)?\s+(?:count|fl\.? oz|fluid ounces?|ounces?|ounce|pounds?|grams?|kilograms?|"
    r"milliliters?|liters?|gallons?|quarts?|pints?)\b(?:\s*\(pack of \d+\))?\s*$",
    re.I,
)
_DETAIL_QTY = re.compile(rf"^\s*{_NUM}\s*({_UNIT_RE}|count|ct)\b", re.I)
_PACK_OF = re.compile(r"pack of (\d+)", re.I)


def _detail_reading(value: str, source: str, allow_one_count: bool) -> Reading | None:
    m = _DETAIL_QTY.match(str(value))
    if not m:
        return None
    n, u = _num(m.group(1)), m.group(2).lower()
    pk = _PACK_OF.search(str(value))
    pack = float(pk.group(1)) if pk else 1.0
    if u in ("count", "ct"):
        if n * pack <= 1 and not allow_one_count:
            return None  # "1 Count" is frequently filler
        return Reading("count", pack, n, "ct", source)
    unit = _unit(u)
    return Reading(TO_BASE[unit][0], pack, n, unit, source)


def _canonical(value: str) -> bool:
    return bool(_CANONICAL.match(str(value)))


def parse_details(details: dict, title_mult: float | None = None, capacity: bool = False) -> list[Reading]:
    """capacity=True (title names a container) drops weight/volume readings: they describe
    what the item holds, not what the price buys."""
    out: list[Reading] = []
    for key, src in (("Size", "size_field"), ("Unit Count", "unit_count")):
        if (v := details.get(key)) and (r := _detail_reading(v, src, allow_one_count=False)):
            if capacity and r.dimension != "count":
                continue
            if not _canonical(v):  # free text like "24L" or "200ct" only corroborates
                r = Reading(r.dimension, r.count, r.size, r.unit, src, strong=False)
            out.append(r)
    for k in ("Item Volume", "Liquid Volume", "Volume"):
        if capacity:
            break
        if (v := details.get(k)) and (r := _detail_reading(v, "volume_field", allow_one_count=False)):
            if r.dimension == "volume":
                out.append(Reading("volume", title_mult or 1.0, r.size, r.unit, "volume_field"))
                break
    for k in ("Sheet Count", "Number of Pieces"):
        if (v := details.get(k)) and str(v).strip().isdigit() and int(v) > 1:
            out.append(Reading("count", 1.0, float(v), "ct", k.lower().replace(" ", "_")))
    for k in ("Number of Items", "Item Package Quantity"):
        if (v := details.get(k)) and str(v).strip().isdigit() and int(v) > 1:
            out.append(Reading("count", 1.0, float(v), "ct", k.lower().replace(" ", "_"), strong=False))
    return out


def extract(item: Item, threshold: float) -> Extraction:
    if _KIT.search(item.title.lower()):
        return Extraction(None, 0.0, "title_is_kit")  # mixed components: no single unit
    title_rs, title_flag = parse_title(item.title)
    if title_flag and title_flag.startswith("title_conflicting"):
        return Extraction(None, 0.3, title_flag)
    title_mult = title_multiplier(item.title)
    mult = next((r.count for r in title_rs if r.count > 1), None)
    detail_rs = parse_details(item.details, mult, capacity=bool(_CAPACITY.search(item.title.lower())))
    readings = tuple(title_rs + detail_rs)
    if not readings:
        return Extraction(None, 0.0, "no_size_found")

    # Group readings that describe the same total in the same dimension.
    groups: list[list[Reading]] = []
    for r in readings:
        for g in groups:
            if g[0].dimension == r.dimension and _agree(g[0].total, r.total):
                g.append(r)
                break
        else:
            groups.append([r])

    def support(g: list[Reading]) -> tuple[int, int]:
        return (len({r.source for r in g if r.strong}), len(g))

    groups.sort(key=support, reverse=True)
    best = groups[0]
    strong_sources = {r.source for r in best if r.strong}
    has_title = any(r.source == "title" for r in best)
    dissent = [r for g in groups[1:] for r in g if r.strong]

    mult_clash = (
        not title_rs and title_mult and best[0].dimension == "count"
        and abs(best[0].total / title_mult - round(best[0].total / title_mult)) > 1e-9
    )

    if not strong_sources:
        conf, flag = 0.4, "only_weak_sources"
    elif dissent or mult_clash:
        conf, flag = 0.3, "sources_disagree"
    elif has_title and len(strong_sources) >= 2:
        conf, flag = 0.95, None
    elif len(strong_sources) >= 2:
        conf, flag = 0.85, None
    elif has_title:
        conf, flag = (0.6, title_flag) if title_flag else (0.8, None)
    else:
        conf, flag = 0.75, None

    if conf < threshold:
        return Extraction(None, conf, flag or "below_threshold", readings)

    # Prefer the title's split into count x size when it is part of the agreeing group.
    rep = next((r for r in best if r.source == "title"), None) or next(r for r in best if r.strong)
    return Extraction(
        PackSize(rep.count, rep.size, rep.unit, rep.dimension, rep.total, conf,
                 tuple(sorted({r.source for r in best}))),
        conf, None, readings,
    )


def load_threshold(path: Path = Path("config/unit_price.json")) -> float:
    return float(json.loads(path.read_text())["confidence_threshold"])
