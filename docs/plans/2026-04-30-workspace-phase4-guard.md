# Workspace Phase-4 Guard Implementation Plan

> **For Claude:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the doc-only Phase 3 → 4 guard in `SKILL.md` with enforced code inside
`workspace.py`. When `mark_phase_complete` is called to advance to `next_phase == "4"`, it
must assert the main notebook has 0 sources. If the count is > 0 it raises `SystemExit` (non-zero
exit), which the existing ABORT RULE already treats as fatal, so Subagent A physically cannot
advance to Phase 4 if it wrote to the main notebook.

**Architecture:** Single file change (`workspace.py`) with new helper `get_notebook_source_count`
wired into `mark_phase_complete`. TDD: write failing tests first, then implement. One commit.

**Tech stack:** Python 3 stdlib + subprocess, pytest. All tests run with
`pytest tests/ -v -m "not live"` from `~/.claude/skills/legal-research/`.

---

## Context

All paths are relative to the skill root: `~/.claude/skills/legal-research/`.

**Baseline:** 15 pre-existing failures in `test_phase_fidelity.py` and `test_setup.py` — these
must remain unchanged after our work.

Run baseline before starting:

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/ -q -m "not live"
```

**Relevant existing code in `references/scripts/workspace.py`:**

- `mark_phase_complete(workspace, phase, next_phase)` — loads `state.json`, appends `phase` to
  `completed_phases`, sets `next_phase`, validates schema, writes back. **This is where the guard
  goes.**
- `load_state(workspace)` — returns parsed `state.json` dict. The `nb_id` key is top-level in
  state.
- CLI: `python3 workspace.py mark-complete <workspace> <phase> <next_phase>` calls
  `mark_phase_complete`.

**Why `nb_id` is available:** `state.json` always has `"nb_id"` by the time Phase 3 completes
(it is written during Phase 2 init). `mark_phase_complete` already loads state, so `nb_id` is
available with no new file reads.

**How the guard integrates:** Phase 3's exit command is:

```bash
python3 $SKILL_ROOT/references/scripts/workspace.py mark-complete $WORKSPACE 3.6 4
```

When this raises `SystemExit` (non-zero exit), the ABORT RULE in `phase-3-research-curation.md`
already says: *"If any script exits non-zero: return `error: <script name> failed` to the
orchestrator and stop."* So no changes are needed to `SKILL.md` or any phase files.

---

## Task 1 — Add guard to `workspace.py` (TDD)

**Files:**
- Modify: `references/scripts/workspace.py`
- Create: `tests/test_workspace_guard.py`

---

### Step 1: Write the failing tests

Create `tests/test_workspace_guard.py`:

```python
"""Tests for the Phase-4 pre-flight guard in workspace.py."""
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

SCRIPT = Path(__file__).parent.parent / "references/scripts/workspace.py"
SCHEMA = Path(__file__).parent.parent / "references/schemas/state.schema.json"


def _load():
    spec = importlib.util.spec_from_file_location("workspace", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_workspace(tmp_path, nb_id="nb-test-123", next_phase="3"):
    """Create a minimal valid workspace with state.json."""
    state = {
        "schema_version": 1,
        "slug": "test-slug",
        "created_at": "2026-04-30T00:00:00+00:00",
        "completed_phases": ["1", "2", "3"],
        "next_phase": next_phase,
        "nb_id": nb_id,
        "scope": {
            "topic": "test topic",
            "jurisdiction": "US",
            "research_queries": [],
        },
    }
    (tmp_path / "state.json").write_text(json.dumps(state))
    return tmp_path


# ── get_notebook_source_count ─────────────────────────────────────────────────

def test_get_notebook_source_count_returns_count():
    mod = _load()
    sources = [{"url": "https://a.com"}, {"url": "https://b.com"}]
    fake = MagicMock(returncode=0, stdout=json.dumps(sources))
    with patch("subprocess.run", return_value=fake):
        assert mod.get_notebook_source_count("nb-123") == 2


def test_get_notebook_source_count_returns_zero_on_empty_list():
    mod = _load()
    fake = MagicMock(returncode=0, stdout=json.dumps([]))
    with patch("subprocess.run", return_value=fake):
        assert mod.get_notebook_source_count("nb-123") == 0


def test_get_notebook_source_count_returns_zero_on_cli_error():
    mod = _load()
    fake = MagicMock(returncode=1, stdout="", stderr="not found")
    with patch("subprocess.run", return_value=fake):
        assert mod.get_notebook_source_count("nb-123") == 0


def test_get_notebook_source_count_returns_zero_on_bad_json():
    mod = _load()
    fake = MagicMock(returncode=0, stdout="not-json")
    with patch("subprocess.run", return_value=fake):
        assert mod.get_notebook_source_count("nb-123") == 0


def test_get_notebook_source_count_returns_zero_on_exception():
    mod = _load()
    with patch("subprocess.run", side_effect=Exception("timeout")):
        assert mod.get_notebook_source_count("nb-123") == 0


# ── mark_phase_complete — guard fires ─────────────────────────────────────────

def test_mark_phase_complete_to_phase4_raises_when_notebook_has_sources(tmp_path):
    """Advancing to phase 4 must fail if the notebook is not empty."""
    mod = _load()
    ws = _make_workspace(tmp_path)
    with patch.object(mod, "get_notebook_source_count", return_value=3):
        with pytest.raises(SystemExit) as exc_info:
            mod.mark_phase_complete(ws, "3.6", "4")
    assert exc_info.value.code != 0


def test_mark_phase_complete_to_phase4_error_message_contains_count(tmp_path):
    """Error message must state the source count so the user can diagnose."""
    mod = _load()
    ws = _make_workspace(tmp_path)
    with patch.object(mod, "get_notebook_source_count", return_value=47):
        with pytest.raises(SystemExit) as exc_info:
            mod.mark_phase_complete(ws, "3.6", "4")
    assert "47" in str(exc_info.value.code)


def test_mark_phase_complete_to_phase4_succeeds_when_notebook_empty(tmp_path):
    """Advancing to phase 4 must succeed when the notebook has 0 sources."""
    mod = _load()
    ws = _make_workspace(tmp_path)
    with patch.object(mod, "get_notebook_source_count", return_value=0):
        state = mod.mark_phase_complete(ws, "3.6", "4")
    assert state["next_phase"] == "4"
    assert "3.6" in state["completed_phases"]


# ── mark_phase_complete — guard does NOT fire for other transitions ────────────

def test_mark_phase_complete_other_transitions_skip_guard(tmp_path):
    """Guard must NOT run when advancing to phases other than 4."""
    mod = _load()
    ws = _make_workspace(tmp_path)
    called = []
    with patch.object(mod, "get_notebook_source_count", side_effect=lambda nb: called.append(nb) or 99):
        mod.mark_phase_complete(ws, "2", "3")
    assert called == [], "guard must not fire for non-phase-4 transitions"


def test_mark_phase_complete_phase3_to_37_skips_guard(tmp_path):
    """Advancing to 3.7 (within Phase 3) must never trigger the guard."""
    mod = _load()
    ws = _make_workspace(tmp_path)
    called = []
    with patch.object(mod, "get_notebook_source_count", side_effect=lambda nb: called.append(nb) or 5):
        mod.mark_phase_complete(ws, "3.6", "3.7")
    assert called == []
```

### Step 2: Run tests to verify they fail

```bash
cd ~/.claire/skills/legal-research
python3 -m pytest tests/test_workspace_guard.py -v 2>&1 | tail -20
```

Expected: all tests FAIL with `AttributeError: module 'workspace' has no attribute 'get_notebook_source_count'`.

---

### Step 3: Implement the guard in `workspace.py`

Add `get_notebook_source_count` and update `mark_phase_complete`. Make the minimum changes —
do not restructure the file.

**Add this function** after the imports, before `_validator()`:

```python
def get_notebook_source_count(nb_id: str) -> int:
    """Return the number of sources currently in the notebook. Returns 0 on any error."""
    import subprocess, json as _json
    try:
        result = subprocess.run(
            ["notebooklm", "source", "list", "-n", nb_id, "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return 0
        sources = _json.loads(result.stdout)
        return len(sources) if isinstance(sources, list) else 0
    except Exception:
        return 0
```

**Update `mark_phase_complete`** — add the guard block at the top of the function, before any
state mutation:

```python
def mark_phase_complete(workspace: Path, phase: str, next_phase: str) -> dict:
    if next_phase == "4":
        state = load_state(workspace)
        nb_id = state.get("nb_id", "")
        count = get_notebook_source_count(nb_id)
        if count > 0:
            raise SystemExit(
                f"Phase 3 guard failed: notebook '{nb_id}' has {count} sources after Phase 3. "
                f"Expected 0. Subagent A wrote directly to the main notebook instead of using "
                f"temp notebooks. Do not proceed to Phase 4. Delete the notebook sources, then "
                f"resume with next_phase='3' in state.json."
            )
    state = load_state(workspace)
    if phase not in state["completed_phases"]:
        state["completed_phases"].append(phase)
    state["next_phase"] = next_phase
    _validator().validate(state)
    (Path(workspace) / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2))
    return state
```

### Step 4: Run tests and verify they pass

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/test_workspace_guard.py -v 2>&1 | tail -20
```

Expected: all 10 tests PASS.

### Step 5: Run full suite and confirm pre-existing failure count is unchanged

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/ -q -m "not live" 2>&1 | tail -5
```

Expected: same 15 failures as baseline; all new tests pass.

### Step 6: Commit

```bash
cd ~/.claude/skills/legal-research
git add references/scripts/workspace.py tests/test_workspace_guard.py
git commit -m "feat: enforce Phase 3 notebook-empty guard in workspace.py mark-complete"
```

---

## Final verification

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/ -q -m "not live" 2>&1 | tail -8
```

Expected: 15 pre-existing failures unchanged; all new tests pass; no regressions.
