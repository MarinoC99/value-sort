"""SPIKE. INDICATIVE ONLY. Freeze the Task 1 title samples (seed 7) with their IDs."""
import json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from matcher import SEED, match, pool, queries

P = pool()
out = {}
for q in queries():
    s = match(P, q)
    out[q] = [{"n": i, "parent_asin": it.parent_asin, "title": it.title}
              for i, it in enumerate(random.Random(SEED).sample(s, min(40, len(s))), 1)]
Path(__file__).with_name("task1_samples.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print({q: len(v) for q, v in out.items()})
