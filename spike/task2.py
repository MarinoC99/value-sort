"""SPIKE task 2. INDICATIVE ONLY: not reproducible as a project result.

Runs the existing pack-size extractor (src/value_sort/unit_price.py, threshold from
config/unit_price.json) over each candidate set. 'vitamin d' is excluded (matcher defect).
"""

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from matcher import match, pool, queries  # noqa: E402
from value_sort.unit_price import extract, load_threshold  # noqa: E402

EXCLUDED = {"vitamin d"}
T = load_threshold(HERE.parent / "config/unit_price.json")
flags = json.loads((HERE / "accessory_flags.json").read_text())["flags"]
samples = json.loads((HERE / "task1_samples.json").read_text())

P = pool()
by_id = {i.parent_asin: i for i in P}
out = {"_note": "SPIKE. INDICATIVE ONLY.", "threshold": T, "queries": {}}
print(f"INDICATIVE ONLY: spike output, not a project result. Threshold {T}.\n")

for q in queries():
    if q in EXCLUDED:
        continue
    s = match(P, q)
    ex = [extract(i, T) for i in s]
    got = [e.result for e in ex if e.result]
    units = Counter(r.unit for r in got)
    dims = Counter(r.dimension for r in got)
    top_dim, top_n = dims.most_common(1)[0] if dims else ("-", 0)
    reasons = Counter(e.flag for e in ex if not e.result)

    flagged = set(flags[q]["flagged"])
    split = {"flagged": [0, 0], "rest": [0, 0]}  # [extracted, n]
    for x in samples[q]:
        k = "flagged" if x["n"] in flagged else "rest"
        split[k][1] += 1
        split[k][0] += bool(extract(by_id[x["parent_asin"]], T).result)

    out["queries"][q] = {
        "set_size": len(s), "extracted": len(got), "share": len(got) / len(s),
        "units": dict(units.most_common()), "dimensions": dict(dims.most_common()),
        "top_dimension_share_of_extracted": top_n / len(got) if got else None,
        "abstain_reasons": dict(reasons.most_common()),
        "sample_split": split,
    }
    print(f"=== {q}: {len(got):,} / {len(s):,} get a pack size ({100 * len(got) / len(s):.1f}%)")
    print(f"    dimensions: {dict(dims.most_common())}  -> top '{top_dim}' = {100 * top_n / max(len(got), 1):.0f}% of extracted")
    print(f"    units:      {dict(units.most_common())}")
    print(f"    abstain:    {dict(reasons.most_common())}")
    fe, fn = split["flagged"]; re_, rn = split["rest"]
    print(f"    sample of 40, by agent's own flags: flagged {fe}/{fn} extracted; rest {re_}/{rn} extracted\n")

(HERE / "out").mkdir(exist_ok=True)
(HERE / "out/task2.json").write_text(json.dumps(out, indent=1))
