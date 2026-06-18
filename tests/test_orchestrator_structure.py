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
    assert "name: legal-research-py" in body
    assert "description:" in body

def test_no_phase_3_through_6_content_inline():
    body = SKILL.read_text()
    for marker in ["Deep Research", "Evidence Registry", "URL Resolution Rules",
                   "Queryability Spot-Check", "IRAC", "Citation Verification Log",
                   "Cross-Examination Protocol", "HTML Template"]:
        assert marker not in body, f"orchestrator leaked phase content: {marker!r}"

def test_dispatch_table_covers_all_phases():
    body = SKILL.read_text()
    for phase_id in ["3-curation","4-indexing","5","5.5","5.6","6"]:
        assert phase_id in body, f"dispatch table missing phase_id={phase_id}"


def test_dispatch_template_has_immediate_start_directive():
    """Dispatch prompt must contain an explicit start directive so subagents
    don't stall after reading the phase file."""
    body = SKILL.read_text()
    assert "YOUR FIRST ACTION" in body or "Start immediately" in body, (
        "SKILL.md dispatch template missing imperative start directive."
    )


PHASE3 = ROOT / "references/phases/phase-3-research-curation.md"

def test_phase3_checkpoint_has_stop_language():
    """Checkpoint 1 must not use 'advance to Phase 4' — that phrase caused
    zombie agents to continue running Phase 4 instead of stopping."""
    body = PHASE3.read_text()
    assert "advance to Phase 4" not in body, (
        "Ambiguous 'advance to Phase 4' found in phase-3 Checkpoint 1. "
        "Replace with explicit STOP language so subagents halt after mark-complete."
    )
    assert any(kw in body for kw in ["STOP.", "return immediately", "return to the orchestrator"]), (
        "phase-3 Checkpoint 1 must include STOP / return-to-orchestrator directive."
    )


def test_dispatch_template_has_scope_boundary():
    """Dispatch prompt must explicitly scope the subagent to one phase only,
    forbidding execution of the next phase (not just file loading)."""
    body = SKILL.read_text()
    assert "THIS PHASE ONLY" in body, (
        "SKILL.md dispatch template is missing 'THIS PHASE ONLY' scope boundary. "
        "Forbidding file loading is insufficient — subagents can continue without loading files."
    )


def test_orchestrator_has_read_before_dispatch_guard():
    """Orchestrator loop must re-read completed_phases from state.json before
    each dispatch and skip if the phase is already done (zombie guard)."""
    body = SKILL.read_text()
    assert "completed_phases[]" in body, (
        "SKILL.md orchestrator loop must read '.completed_phases[]' from state.json "
        "to guard against zombie agents that already advanced the phase."
    )
    assert "do not dispatch" in body.lower(), (
        "SKILL.md must instruct the orchestrator not to dispatch if the phase is "
        "already in completed_phases."
    )


def test_phase3_has_immediate_start_directive():
    """Phase 3 must contain an explicit 'run this first' directive to prevent
    subagents from reading the file and then stopping without executing."""
    body = PHASE3.read_text()
    assert "YOUR FIRST ACTION" in body or "Run this command first" in body, (
        "phase-3-research-curation.md is missing an immediate-start directive. "
        "Subagents read the file but then stop — an imperative opening prevents this."
    )
