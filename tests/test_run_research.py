"""Tests for run_research.py helper functions."""
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).parent.parent / "references/scripts/run_research.py"


def _load():
    spec = importlib.util.spec_from_file_location("run_research", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── run_cmd ──────────────────────────────────────────────────────────────────

def test_run_cmd_returns_stdout_on_success():
    mod = _load()
    fake = MagicMock(returncode=0, stdout="hello\n", stderr="")
    with patch("subprocess.run", return_value=fake):
        result = mod.run_cmd("echo hello")
    assert result == "hello"


def test_run_cmd_raises_on_nonzero_exit():
    mod = _load()
    fake = MagicMock(returncode=1, stdout="", stderr="something went wrong")
    with patch("subprocess.run", return_value=fake):
        try:
            mod.run_cmd("false")
            assert False, "Expected RuntimeError"
        except RuntimeError as exc:
            assert "something went wrong" in str(exc)


def test_run_cmd_check_false_does_not_raise():
    mod = _load()
    fake = MagicMock(returncode=1, stdout="partial output", stderr="err")
    with patch("subprocess.run", return_value=fake):
        result = mod.run_cmd("false", check=False)
    assert result == "partial output"


# ── is_still_pending ─────────────────────────────────────────────────────────

def test_is_still_pending_true_when_status_in_progress():
    mod = _load()
    payload = json.dumps({"status": "in_progress", "tasks": []})
    assert mod.is_still_pending(payload) is True


def test_is_still_pending_true_when_status_pending():
    mod = _load()
    payload = json.dumps({"status": "pending"})
    assert mod.is_still_pending(payload) is True


def test_is_still_pending_false_when_status_completed():
    mod = _load()
    payload = json.dumps({"status": "completed", "tasks": [{"sources": []}]})
    assert mod.is_still_pending(payload) is False


def test_is_still_pending_false_when_status_done():
    mod = _load()
    payload = json.dumps({"status": "done"})
    assert mod.is_still_pending(payload) is False


def test_is_still_pending_falls_back_to_string_match_on_bad_json():
    mod = _load()
    assert mod.is_still_pending("Research is in_progress...") is True
    assert mod.is_still_pending("All done.") is False


def test_is_still_pending_treats_error_response_as_not_pending():
    """An error JSON with no status/in_progress should NOT be treated as pending."""
    mod = _load()
    payload = json.dumps({"error": "notebook not found", "code": 404})
    assert mod.is_still_pending(payload) is False
