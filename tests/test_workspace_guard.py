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
            "report_language": "English",
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
