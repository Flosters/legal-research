"""
Each phase sub-skill must contain *verbatim* every paragraph of its original
phase section in the rhino SKILL.md.

We test by extracting the phase section from the original SKILL.md between
`## Phase <N>` markers, then asserting every non-blank line of that section
(ignoring markdown heading level and leading/trailing whitespace) appears
somewhere in the corresponding phase file. This catches accidental deletion
during migration.
"""
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).parent.parent
ORIG = Path("/Users/agustinsilvazambrano/.claude/skills/notebooklm-legal-research-rhino/SKILL.md")
PHASE_DIR = ROOT / "references/phases"

# Lines from the original that were intentionally dropped or replaced during
# migration (halt-directive blocks, etc.). These are excluded from the
# fidelity requirement. Match by substring.
REPLACED_SUBSTRINGS = [
    "CRITICAL SYSTEM DIRECTIVE",
    "STOP EXECUTION HERE",
    "Do not assume a choice",
    "Or reply `continue` to proceed",
    "wait for the user",
    "Wait for the user",
    "HARD HALT",
]

# Path remaps applied during migration. Before testing membership we rewrite
# each original line with every remap; if either the raw or remapped form
# appears in the new file, the line counts as preserved.
PATH_REMAPS = [
    ("/Users/agustinsilvazambrano/.claude/skills/notebooklm-legal-research-rhino/references/jurisdiction-filter.py",
     "$SKILL_ROOT/references/scripts/jurisdiction-filter.py"),
    ("/Users/agustinsilvazambrano/.claude/skills/notebooklm-legal-research-rhino/references/batch-import.py",
     "$SKILL_ROOT/references/scripts/batch-import.py"),
    ("references/jurisdiction-filter.py",
     "$SKILL_ROOT/references/scripts/jurisdiction-filter.py"),
    ("references/batch-import.py",
     "$SKILL_ROOT/references/scripts/batch-import.py"),
    ("references/source-priority.md",
     "$SKILL_ROOT/references/source-priority.md"),
    ("references/analysis-prompts.md",
     "$SKILL_ROOT/references/analysis-prompts.md"),
    ("references/citation-styles.md",
     "$SKILL_ROOT/references/citation-styles.md"),
    ("references/verification-protocol.md",
     "$SKILL_ROOT/references/verification-protocol.md"),
    ("references/output-templates.md",
     "$SKILL_ROOT/references/output-templates.md"),
]

# (phase_header_regex, dest_file)
PHASES = [
    (r"^## Phase 3 —", "phase-3-research-curation.md"),
    (r"^## Phase 3\.5 —", "phase-3-research-curation.md"),
    (r"^## Phase 3\.6 —", "phase-3-research-curation.md"),
    (r"^## Phase 3\.7 —", "phase-3-7-primary-import.md"),
    (r"^## Phase 4 —", "phase-4-import-queryability.md"),
    (r"^## Phase 4\.1 —", "phase-4-import-queryability.md"),
    (r"^## Phase 4\.5 —", "phase-4-import-queryability.md"),
    (r"^## Phase 5 —", "phase-5-analysis.md"),
    (r"^## Phase 5\.5 —", "phase-5-5-citation-verification.md"),
    (r"^## Phase 5\.6 —", "phase-5-6-cross-examination.md"),
    (r"^## Phase 6 —", "phase-6-report.md"),
]


def _extract_section(src: str, start_re: str) -> list[str]:
    lines = src.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if re.match(start_re, ln):
            start = i
            break
    assert start is not None, f"phase marker not found: {start_re}"
    # End at the next `## Phase ` heading (any phase, different from start)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## Phase ") and not re.match(start_re, lines[j]):
            return lines[start:j]
    return lines[start:]


@pytest.mark.parametrize("start_re,fname", PHASES)
def test_phase_content_preserved(start_re, fname):
    dest = PHASE_DIR / fname
    assert dest.exists(), f"phase file missing: {fname}"
    original = ORIG.read_text()
    new = dest.read_text()
    section = _extract_section(original, start_re)
    missing = []
    for ln in section:
        s = ln.strip()
        if not s or s == "---":
            continue
        if any(skip in s for skip in REPLACED_SUBSTRINGS):
            continue
        # Drop the heading level prefix (## vs ###) so we allow rewrapping
        s_no_hash = re.sub(r"^#+\s*", "", s)
        # Also try after applying each known path remap
        variants = {s, s_no_hash}
        for old, new_path in PATH_REMAPS:
            if old in s:
                variants.add(s.replace(old, new_path))
                variants.add(s_no_hash.replace(old, new_path))
        if not any(v in new for v in variants):
            missing.append(s)
    assert not missing, (
        f"{fname} missing {len(missing)} lines from original phase section.\n"
        f"First 5 missing:\n" + "\n".join(missing[:5]))
