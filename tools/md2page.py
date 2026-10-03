"""Portfolio page generator: drafts/portfolio_page.md -> the personal site's value-sort.html.

Usage:
  python3 tools/md2page.py drafts/portfolio_page.md <site>/value-sort.html
  python3 tools/md2page.py --check drafts/portfolio_page.md <site>/value-sort.html

The first form writes the page. The second writes nothing: it checks that the page's
visible text matches the markdown word for word (markdown syntax, link targets and the
site's "Projects" back-link aside) and exits non-zero if not.

Handles exactly the constructs the page uses: #/##/### headings, paragraphs, **bold**,
*italic* (whole-paragraph), [links](url), `code`, ordered/unordered lists with continuation lines,
a pipe table, and --- rules. Text is HTML-escaped and otherwise left verbatim. The page
shell (header, nav, footer, stylesheet) matches the personal site's other pages; the
site's site.css supplies the .article styles.
"""
import html
import re
import sys


def check(src: str, page: str) -> bool:
    md = open(src, encoding="utf-8").read()
    pg = open(page, encoding="utf-8").read()
    main = pg[pg.index("<main"):pg.index("</main>")]
    t = re.sub(r"\[([^\]]+)\]\([^)\s]+\)", r"\1", md)
    t = re.sub(r"(?m)^#+ ", "", t)
    t = re.sub(r"(?m)^\|?[-| ]+\|?$", "", t)
    t = re.sub(r"(?m)^(\d+)\. (?=\*\*)", "", t)
    t = re.sub(r"(?m)^- ", "", t)
    t = re.sub(r"(?m)^---$", "", t).replace("**", "").replace("|", " ").replace("*", "").replace("`", "")
    title = md.split("\n", 1)[0].lstrip("# ")
    name, _, sub = title.partition(": ")
    a = " ".join(t.split()).replace(f"{name}: {sub}", f"{name} {sub[:1].upper() + sub[1:]}", 1).split()
    h = re.sub(r"</?(strong|em|a|code)( [^>]*)?>", "", main)
    h = [w for w in html.unescape(re.sub(r"<[^>]+>", " ", h)).split() if w != "Projects"]
    print(f"word-for-word identical: {a == h} ({len(a)} vs {len(h)} words)")
    return a == h


if sys.argv[1] == "--check":
    sys.exit(0 if check(sys.argv[2], sys.argv[3]) else 1)

src, out = sys.argv[1], sys.argv[2]
lines = open(src, encoding="utf-8").read().split("\n")


def inline(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", t)
    return t


blocks, i = [], 0
while i < len(lines):
    l = lines[i]
    if not l.strip():
        i += 1
        continue
    if l.startswith("# "):
        blocks.append(("h1", l[2:].strip())); i += 1; continue
    if l.startswith("### "):
        blocks.append(("h3", l[4:].strip())); i += 1; continue
    if l.startswith("## "):
        blocks.append(("h2", l[3:].strip())); i += 1; continue
    if l.strip() == "---":
        blocks.append(("hr", "")); i += 1; continue
    if l.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r"-+", c) for c in cells):
                rows.append(cells)
            i += 1
        blocks.append(("table", rows)); continue
    m = re.match(r"^(\d+\.|-) ", l)
    if m:
        kind = "ol" if m.group(1)[0].isdigit() else "ul"
        items = []
        while i < len(lines) and lines[i].strip():
            mm = re.match(r"^(\d+\.|-) (.*)", lines[i])
            if mm:
                items.append(mm.group(2))
            else:
                items[-1] += " " + lines[i].strip()
            i += 1
        blocks.append((kind, items)); continue
    para = []
    while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||---$|\d+\. |- )", lines[i]):
        para.append(lines[i].strip()); i += 1
    blocks.append(("p", " ".join(para)))

# The source title "Value Sort: re-ranking ..." becomes an h1 plus subtitle; the first
# paragraph after it is the lede; the Status paragraph is a note box; the closing
# italic paragraph is the page's source note.
title = blocks[0][1]
name, _, sub = title.partition(": ")
body = []
first_p_done = False
for kind, val in blocks[1:]:
    if kind == "p":
        if not first_p_done:
            body.append(f'  <p class="lede">{inline(val)}</p>'); first_p_done = True
        elif val.startswith("**Status:"):
            body.append(f'  <p class="status-note">{inline(val)}</p>')
        elif val.startswith("*") and val.endswith("*") and not val.startswith("**"):
            body.append(f'  <p class="source-note">{inline(val[1:-1])}</p>')
        else:
            body.append(f"  <p>{inline(val)}</p>")
    elif kind == "h2":
        body.append(f"  <h2>{inline(val)}</h2>")
    elif kind == "h3":
        body.append(f"  <h3>{inline(val)}</h3>")
    elif kind == "hr":
        body.append("  <hr>")
    elif kind in ("ol", "ul"):
        body.append(f"  <{kind}>" + "".join(f"\n    <li>{inline(x)}</li>" for x in val) + f"\n  </{kind}>")
    elif kind == "table":
        rows = val
        head, rest = rows[0], rows[1:]
        has_head = any(c for c in head)
        t = ['  <div class="table-wrap"><table>']
        if has_head:
            t.append("    <thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead>")
        else:
            rest = rows[1:] if not any(head) else rows
        t.append("    <tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rest) + "</tbody>")
        t.append("  </table></div>")
        body.append("\n".join(t))

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(name)} &mdash; Marino Coric</title>
<meta name="description" content="{html.escape(sub[:1].upper() + sub[1:])}: an independent student project using the public Amazon Reviews 2023 dataset.">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="stylesheet" href="site.css">
</head>
<body>

<header class="topbar">
  <div class="shell">
    <a class="brand" href="index.html">Marino Coric</a>
    <nav aria-label="Main">
      <ul class="nav">
        <li><a href="index.html">Home</a></li>
        <li><a href="resume.html">Resume</a></li>
        <li><a href="projects.html" aria-current="page">Projects</a></li>
      </ul>
    </nav>
  </div>
</header>

<main class="shell article">

  <p class="eyebrow"><a href="projects.html">Projects</a></p>
  <h1>{inline(name)}</h1>
  <p class="subtitle">{inline(sub[:1].upper() + sub[1:])}</p>
{chr(10).join(body)}

</main>

<footer class="shell">
  © 2026 Marino Coric
</footer>

<script src="ask-my-site.js"></script>
</body>
</html>
"""
open(out, "w", encoding="utf-8").write(page)
print("blocks:", [k for k, _ in blocks])
