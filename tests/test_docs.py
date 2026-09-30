"""README.md and SPEC.md must carry the identical status banner (DECISIONS.md #44)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def status_banner(path: Path) -> str:
    """The first blockquote paragraph that starts with **Status:"""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("> **Status:"))
    end = start
    while end < len(lines) and lines[end].startswith(">") and lines[end].strip() != ">":
        end += 1
    return "\n".join(lines[start:end])


def test_readme_and_spec_status_banners_match():
    assert status_banner(ROOT / "README.md") == status_banner(ROOT / "SPEC.md")
