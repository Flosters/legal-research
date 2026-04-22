import hashlib
from pathlib import Path

ORIG = Path("/Users/agustinsilvazambrano/.claude/skills/notebooklm-legal-research-rhino/references")
NEW = Path(__file__).parent.parent / "references"

PAIRS = [
    ("jurisdiction-filter.py", NEW / "scripts" / "jurisdiction-filter.py"),
    ("batch-import.py",        NEW / "scripts" / "batch-import.py"),
    ("source-priority.md",     NEW / "source-priority.md"),
    ("analysis-prompts.md",    NEW / "analysis-prompts.md"),
    ("citation-styles.md",     NEW / "citation-styles.md"),
    ("verification-protocol.md", NEW / "verification-protocol.md"),
    ("output-templates.md",    NEW / "output-templates.md"),
]


def _hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_every_reference_copied_bit_for_bit():
    for name, dest in PAIRS:
        src = ORIG / name
        assert dest.exists(), f"missing: {dest}"
        assert _hash(src) == _hash(dest), f"content drift: {dest.name}"
