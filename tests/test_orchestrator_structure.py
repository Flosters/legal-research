from pathlib import Path

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "SKILL.md"

REQUIRED_SECTIONS = [
    "## Language Rules",
    "## Resume Handler",
    "## Prerequisites",
    "## Phase 1 — Scope + Checklist (inline)",
    "## Phase 2 — Notebook Creation (inline)",
    "## Dispatch Table",
    "## Subagent Dispatch Protocol",
    "## Error Handling",
]

def test_skill_exists():
    assert SKILL.exists()

def test_skill_under_300_lines():
    n = sum(1 for _ in SKILL.read_text().splitlines())
    assert n <= 300, f"orchestrator is {n} lines; target ≤300"

def test_required_sections_present():
    body = SKILL.read_text()
    missing = [s for s in REQUIRED_SECTIONS if s not in body]
    assert not missing, f"missing sections: {missing}"

def test_frontmatter_valid():
    body = SKILL.read_text()
    assert body.startswith("---\n")
    assert "name: notebooklm-legal-research-hybrid" in body
    assert "description:" in body

def test_no_phase_3_through_6_content_inline():
    body = SKILL.read_text()
    for marker in ["Deep Research", "Evidence Registry", "URL Resolution Rules",
                   "Queryability Spot-Check", "IRAC", "Citation Verification Log",
                   "Cross-Examination Protocol", "HTML Template"]:
        assert marker not in body, f"orchestrator leaked phase content: {marker!r}"

def test_dispatch_table_covers_all_phases():
    body = SKILL.read_text()
    for phase_id in ["3-curation","3.7","4-indexing","5","5.5","5.6","6"]:
        assert phase_id in body, f"dispatch table missing phase_id={phase_id}"
