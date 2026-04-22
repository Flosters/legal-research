# tests/test_no_halt_directives.py
from pathlib import Path

ROOT = Path(__file__).parent.parent

BLOCKED_PATTERNS = [
    "🛑 CRITICAL SYSTEM DIRECTIVE",
    "STOP EXECUTION HERE",
    "Do not assume a choice",
    "Or reply `continue` to proceed",
]

def _all_md_files():
    for p in (ROOT / "SKILL.md",):
        yield p
    for p in (ROOT / "references/phases").glob("*.md"):
        yield p

def test_no_halt_directives_anywhere():
    offenders = []
    for f in _all_md_files():
        body = f.read_text()
        for pat in BLOCKED_PATTERNS:
            if pat in body:
                offenders.append((f.name, pat))
    assert not offenders, (
        "hybrid skill still contains halt directives from original:\n" +
        "\n".join(f"  {n}: {p!r}" for n, p in offenders))
