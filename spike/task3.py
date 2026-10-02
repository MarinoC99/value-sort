"""SPIKE task 3. INDICATIVE ONLY: not reproducible as a project result.

Two axes per candidate set, no composite score:
  y = z(CAR), CAR with candidate-set priors (DECISIONS #12), standardized over the whole set
  x = -z(ln unit price), unit price = price / (count x size) for items in the set's
      DOMINANT dimension only, standardized over the items that have a unit price
Everything without a dominant-dimension unit price is fail-open: kept, flagged, plotted in
a margin strip. Accessory flags are the agent's own Task 1 judgments (sampled titles only).
"""

import csv
import html
import json
import math
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from matcher import match, pool  # noqa: E402
from value_sort.car import car, priors_for  # noqa: E402
from value_sort.priors import load_fallback  # noqa: E402
from value_sort.unit_price import TO_BASE, extract, load_threshold  # noqa: E402

QUERIES = ["protein powder", "hand sanitizer"]  # primary, secondary (user's choice)
DISPLAY = {"weight": ("oz", TO_BASE["oz"][1]), "volume": ("fl oz", TO_BASE["fl oz"][1]),
           "count": ("ct", 1.0)}
T = load_threshold(ROOT / "config/unit_price.json")
FLAGS = json.loads((HERE / "accessory_flags.json").read_text())["flags"]
SAMPLES = json.loads((HERE / "task1_samples.json").read_text())


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=0)


def build(q: str, P) -> tuple[pd.DataFrame, dict]:
    cands = match(P, q)
    pri = priors_for(cands, load_fallback("Health_and_Household"))
    flagged_ids = {x["parent_asin"] for x in SAMPLES[q] if x["n"] in set(FLAGS[q]["flagged"])}
    sampled_ids = {x["parent_asin"] for x in SAMPLES[q]}
    ex = {i.parent_asin: extract(i, T) for i in cands}
    dims = Counter(e.result.dimension for e in ex.values() if e.result)
    dom = dims.most_common(1)[0][0]
    unit, per = DISPLAY[dom]

    rows = []
    for i in cands:
        e = ex[i.parent_asin]
        r = e.result
        if r is None:
            fo, why, up = True, f"no pack size ({e.flag})", None
        elif r.dimension != dom:
            fo, why, up = True, f"non-dominant dimension ({r.dimension})", None
        else:
            fo, why, up = False, "", i.price / (r.total_base / per)
        rows.append({
            "parent_asin": i.parent_asin, "title": i.title, "price": i.price,
            "average_rating": i.average_rating, "rating_number": i.rating_number,
            "car": car(i.average_rating, i.rating_number, pri.C, pri.m),
            "pack": None if r is None else f"{r.count:g} x {r.size:g} {r.unit}",
            "unit_price": up, "unit": f"$/{unit}" if up is not None else "",
            "fail_open": fo, "fail_open_reason": why,
            "sampled": i.parent_asin in sampled_ids,
            "accessory_flag": (i.parent_asin in flagged_ids) if i.parent_asin in sampled_ids else None,
        })
    df = pd.DataFrame(rows)
    df["z_car"] = zscore(df["car"])
    has = df["unit_price"].notna()
    df.loc[has, "z_value"] = -zscore(df.loc[has, "unit_price"].map(math.log))

    both = df[has]
    quad = {
        "credible_and_cheap (+,+)": int(((both.z_car > 0) & (both.z_value > 0)).sum()),
        "credible_but_pricey (+,-)": int(((both.z_car > 0) & (both.z_value <= 0)).sum()),
        "cheap_but_less_credible (-,+)": int(((both.z_car <= 0) & (both.z_value > 0)).sum()),
        "less_credible_and_pricey (-,-)": int(((both.z_car <= 0) & (both.z_value <= 0)).sum()),
    }
    clear = lambda a, b: int((a & b).sum())
    summary = {
        "query": q, "set_size": len(df), "dominant_dimension": dom, "unit": f"$/{unit}",
        "priors": {"C": pri.C, "m": pri.m, "source": pri.source, "n_rated": pri.n_rated,
                   "flagged_under_30": pri.flagged},
        "with_unit_price": int(has.sum()), "fail_open": int((~has).sum()),
        "fail_open_reasons": dict(Counter(df.loc[~has, "fail_open_reason"].str.split(" \\(").str[0])),
        "quadrants": quad,
        "off_diagonal_share": (quad["credible_but_pricey (+,-)"] + quad["cheap_but_less_credible (-,+)"]) / len(both),
        "clearly_off_diagonal_|z|>0.5_both": clear((both.z_car > 0.5), (both.z_value < -0.5))
        + clear((both.z_car < -0.5), (both.z_value > 0.5)),
        "pearson_zcar_zvalue": float(both.z_car.corr(both.z_value)),
        "spearman_zcar_zvalue": float(both.z_car.rank().corr(both.z_value.rank())),  # Pearson on ranks; no scipy
        "unit_price_range": [float(both.unit_price.min()), float(both.unit_price.median()), float(both.unit_price.max())],
        "sampled_accessories_with_unit_price": int((both.accessory_flag == True).sum()),  # noqa: E712
        "sampled_accessories_fail_open": int((df.loc[~has, "accessory_flag"] == True).sum()),  # noqa: E712
    }
    return df, summary


# ---------------------------------------------------------------- plotting (plain SVG)
W, H, ML, MR, MT, MB, STRIP = 760, 520, 150, 24, 40, 56, 70


def svg_for(df: pd.DataFrame, s: dict) -> str:
    has = df.z_value.notna()
    ys = df.z_car
    ylo, yhi = math.floor(ys.min() * 2) / 2 - 0.25, math.ceil(ys.max() * 2) / 2 + 0.25
    xv = df.loc[has, "z_value"]
    xlo, xhi = math.floor(xv.min() * 2) / 2 - 0.25, math.ceil(xv.max() * 2) / 2 + 0.25
    px = lambda x: ML + (x - xlo) / (xhi - xlo) * (W - ML - MR)
    py = lambda y: MT + (yhi - y) / (yhi - ylo) * (H - MT - MB)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(s["query"])} scatter">']
    # strip panel
    sx0, sx1 = 12, 12 + STRIP
    out.append(f'<rect x="{sx0}" y="{MT}" width="{STRIP}" height="{H - MT - MB}" class="strip"/>')
    out.append(f'<text x="{(sx0 + sx1) / 2}" y="{H - MB + 18}" class="lab" text-anchor="middle">fail-open</text>')
    out.append(f'<text x="{(sx0 + sx1) / 2}" y="{H - MB + 32}" class="lab" text-anchor="middle">n={int((~has).sum())}</text>')
    # grid + quadrant lines
    for t in range(math.ceil(ylo), math.floor(yhi) + 1):
        out.append(f'<line x1="{ML}" x2="{W - MR}" y1="{py(t):.1f}" y2="{py(t):.1f}" class="grid"/>'
                   f'<text x="{ML - 6}" y="{py(t) + 4:.1f}" class="tick" text-anchor="end">{t}</text>')
    for t in range(math.ceil(xlo), math.floor(xhi) + 1):
        out.append(f'<line y1="{MT}" y2="{H - MB}" x1="{px(t):.1f}" x2="{px(t):.1f}" class="grid"/>'
                   f'<text y="{H - MB + 16}" x="{px(t):.1f}" class="tick" text-anchor="middle">{t}</text>')
    out.append(f'<line x1="{px(0):.1f}" x2="{px(0):.1f}" y1="{MT}" y2="{H - MB}" class="zero"/>'
               f'<line x1="{ML}" x2="{W - MR}" y1="{py(0):.1f}" y2="{py(0):.1f}" class="zero"/>')
    q = s["quadrants"]
    for x, y, a, k, name in [(W - MR - 6, MT + 14, "end", "credible_and_cheap (+,+)", "credible & cheap"),
                             (ML + 6, MT + 14, "start", "credible_but_pricey (+,-)", "credible, pricier"),
                             (W - MR - 6, H - MB - 8, "end", "cheap_but_less_credible (-,+)", "cheap, less credible"),
                             (ML + 6, H - MB - 8, "start", "less_credible_and_pricey (-,-)", "less credible & pricier")]:
        out.append(f'<text x="{x}" y="{y}" text-anchor="{a}" class="quad">{name}: {q[k]}</text>')
    out.append(f'<text x="{(ML + W - MR) / 2}" y="{H - 14}" class="axis" text-anchor="middle">'
               f'−z(ln unit price, {s["unit"]})  → cheaper per unit</text>')
    out.append(f'<text transform="translate({ML - 34},{(MT + H - MB) / 2}) rotate(-90)" class="axis" '
               f'text-anchor="middle">z(CAR)  → more credible rating</text>')

    def tip(r):
        up = f'${r.unit_price:.3f}{r.unit[1:]}' if pd.notna(r.unit_price) else r.fail_open_reason
        acc = " · ACCESSORY-FLAGGED" if r.accessory_flag is True else ""
        return html.escape(f"{r.title[:90]}\n{r.average_rating}★ from {r.rating_number:,} · CAR {r.car:.3f} · "
                           f"${r.price:.2f} · {r.pack or 'no pack size'} · {up}{acc}")

    # fail-open strip points: deterministic jitter by row index
    for k, r in enumerate(df[~has].itertuples()):
        x = sx0 + 8 + (k * 37 % (STRIP - 16))
        cls = "acc" if r.accessory_flag is True else "fo"
        shape = (f'<rect x="{x - 4.5:.1f}" y="{py(r.z_car) - 4.5:.1f}" width="9" height="9" transform="rotate(45 {x:.1f} {py(r.z_car):.1f})" class="{cls}"/>'
                 if cls == "acc" else f'<circle cx="{x:.1f}" cy="{py(r.z_car):.1f}" r="4" class="{cls}"/>')
        out.append(f'<g>{shape}<title>{tip(r)}</title></g>')
    # plotted points, accessories drawn last so they sit on top
    pts = df[has].assign(_a=df.accessory_flag.eq(True)).sort_values("_a")
    for r in pts.itertuples():
        x, y = px(r.z_value), py(r.z_car)
        if r.accessory_flag is True:
            mark = f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" transform="rotate(45 {x:.1f} {y:.1f})" class="acc"/>'
        else:
            mark = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="pt"/>'
        out.append(f'<g>{mark}<title>{tip(r)}</title></g>')
    out.append("</svg>")
    return "\n".join(out)


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Spike scatter</title>
<style>
:root{{--surface-1:#fcfcfb;--surface-2:#f0efec;--text-primary:#0b0b0b;--text-secondary:#52514e;
--grid:#e4e3df;--zero:#9a998f;--series-1:#2a78d6;--series-2:#eb6834;--neutral:#a3a29a}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface-1:#1a1a19;--surface-2:#262624;
--text-primary:#fff;--text-secondary:#c3c2b7;--grid:#30302d;--zero:#6f6e67;--series-1:#3987e5;--series-2:#d95926;--neutral:#6f6e67}}}}
:root[data-theme="dark"]{{--surface-1:#1a1a19;--surface-2:#262624;--text-primary:#fff;--text-secondary:#c3c2b7;
--grid:#30302d;--zero:#6f6e67;--series-1:#3987e5;--series-2:#d95926;--neutral:#6f6e67}}
body{{background:var(--surface-1);color:var(--text-primary);font:14px/1.45 system-ui,sans-serif;margin:0;padding:16px}}
main{{max-width:800px;margin:0 auto}} svg{{width:100%;height:auto;display:block}}
.banner{{border:1px solid var(--zero);padding:8px 12px;border-radius:6px;color:var(--text-secondary)}}
.grid{{stroke:var(--grid);stroke-width:1}} .zero{{stroke:var(--zero);stroke-width:1}}
.tick,.lab{{fill:var(--text-secondary);font-size:11px}} .axis{{fill:var(--text-secondary);font-size:12px}}
.quad{{fill:var(--text-secondary);font-size:12px;font-weight:600}}
.strip{{fill:var(--surface-2)}}
.pt{{fill:var(--series-1);fill-opacity:.55;stroke:var(--surface-1);stroke-width:1.5}}
.fo{{fill:var(--neutral);fill-opacity:.6;stroke:var(--surface-1);stroke-width:1.5}}
.acc{{fill:var(--series-2);stroke:var(--surface-1);stroke-width:2}}
.legend span{{display:inline-flex;align-items:center;gap:6px;margin-right:16px;color:var(--text-secondary)}}
.sw{{width:10px;height:10px;display:inline-block}}
table{{border-collapse:collapse;font-size:13px}} td,th{{padding:3px 10px;border-bottom:1px solid var(--grid);text-align:left}}
</style></head><body><main>
<p class="banner"><strong>INDICATIVE ONLY.</strong> Spike output on branch spike/step7, not a project result.
No composite score is computed. Hover a point for its title and values.</p>
{body}
</main></body></html>"""


def main() -> None:
    P = pool()
    sections, summaries = [], []
    (HERE / "out").mkdir(exist_ok=True)
    for q in QUERIES:
        df, s = build(q, P)
        summaries.append(s)
        slug = q.replace(" ", "_")
        df.drop(columns=[]).to_csv(HERE / f"out/task3_{slug}.csv", index=False, quoting=csv.QUOTE_MINIMAL)
        p = s["priors"]
        sections.append(
            f'<h2>{html.escape(q)}</h2>'
            f'<p>{s["set_size"]:,} items · candidate-set priors C = {p["C"]:.4f}, m = {p["m"]:g} '
            f'({p["source"]}{", FLAGGED: under 30 rated" if p["flagged_under_30"] else ""}) · '
            f'unit price in the dominant dimension ({s["dominant_dimension"]}, {s["unit"]}) for '
            f'{s["with_unit_price"]:,}; {s["fail_open"]:,} fail open.</p>'
            '<p class="legend"><span><i class="sw" style="background:var(--series-1);border-radius:50%"></i>has unit price</span>'
            '<span><i class="sw" style="background:var(--series-2);transform:rotate(45deg)"></i>accessory-flagged (sampled titles only)</span>'
            '<span><i class="sw" style="background:var(--neutral);border-radius:50%"></i>fail-open (margin strip, y = z(CAR))</span></p>'
            + svg_for(df, s)
            + f'<p>Spearman ρ(z(CAR), −z(ln unit price)) = {s["spearman_zcar_zvalue"]:.3f}; '
              f'off-diagonal share {100 * s["off_diagonal_share"]:.1f}%; '
              f'clearly off-diagonal (|z| &gt; 0.5 on both axes): {s["clearly_off_diagonal_|z|>0.5_both"]}.</p>')
    (HERE / "out/task3_scatter.html").write_text(PAGE.format(body="\n".join(sections)), encoding="utf-8")
    (HERE / "out/task3_summary.json").write_text(json.dumps(summaries, indent=1))
    print("INDICATIVE ONLY: spike output, not a project result.")
    print(json.dumps(summaries, indent=1))


if __name__ == "__main__":
    main()
