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


import argparse
import tempfile
from pathlib import Path


# ── run_gap_query ─────────────────────────────────────────────────────────────

def test_run_gap_query_creates_temp_notebook_with_query():
    """Temp notebook is created, add-research called on it (not main nb), then deleted."""
    mod = _load()
    calls = []

    def fake_run_cmd(cmd, check=True):
        calls.append(cmd)
        if "create" in cmd:
            return '{"id": "temp-nb-123"}'
        if "research status" in cmd:
            return '{"status": "done"}'
        return ""

    with patch.object(mod, "run_cmd", side_effect=fake_run_cmd), \
         patch.object(mod, "time") as mock_time:
        mock_time.sleep = lambda _: None
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_path = f.name
        mod.run_gap_query("OFAC sanctions list", "main-nb-456", out_path)

    add_research_calls = [c for c in calls if "add-research" in c]
    assert len(add_research_calls) == 1
    assert "temp-nb-123" in add_research_calls[0]
    assert "main-nb-456" not in add_research_calls[0]


def test_run_gap_query_saves_status_to_out_path():
    """Status JSON is written to the --out path."""
    mod = _load()

    def fake_run_cmd(cmd, check=True):
        if "create" in cmd:
            return '{"id": "temp-nb-abc"}'
        if "research status" in cmd:
            return '{"status": "done", "sources": [{"url": "https://ofac.treasury.gov"}]}'
        return ""

    with patch.object(mod, "run_cmd", side_effect=fake_run_cmd), \
         patch.object(mod, "time") as mock_time:
        mock_time.sleep = lambda _: None
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_path = f.name
        mod.run_gap_query("sanctions", "main-nb-456", out_path)

    content = Path(out_path).read_text()
    assert "ofac.treasury.gov" in content


def test_run_gap_query_deletes_temp_notebook_on_success():
    """Temp notebook is deleted after successful completion."""
    mod = _load()
    calls = []

    def fake_run_cmd(cmd, check=True):
        calls.append(cmd)
        if "create" in cmd:
            return '{"id": "temp-nb-xyz"}'
        if "research status" in cmd:
            return '{"status": "done"}'
        return ""

    with patch.object(mod, "run_cmd", side_effect=fake_run_cmd), \
         patch.object(mod, "time") as mock_time:
        mock_time.sleep = lambda _: None
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_path = f.name
        mod.run_gap_query("sanctions", "main-nb-456", out_path)

    delete_calls = [c for c in calls if "delete" in c and "temp-nb-xyz" in c]
    assert len(delete_calls) == 1


def test_run_gap_query_deletes_temp_notebook_on_error():
    """Temp notebook is deleted even when add-research raises."""
    mod = _load()
    calls = []

    def fake_run_cmd(cmd, check=True):
        calls.append(cmd)
        if "create" in cmd:
            return '{"id": "temp-nb-err"}'
        if "add-research" in cmd and check:
            raise RuntimeError("network error")
        return ""

    with patch.object(mod, "run_cmd", side_effect=fake_run_cmd), \
         patch.object(mod, "time") as mock_time:
        mock_time.sleep = lambda _: None
        try:
            mod.run_gap_query("sanctions", "main-nb-456", "/tmp/out.json")
        except RuntimeError:
            pass

    delete_calls = [c for c in calls if "delete" in c and "temp-nb-err" in c]
    assert len(delete_calls) == 1


# ── main — gap mode ───────────────────────────────────────────────────────────

def test_main_invokes_gap_mode_with_flags(tmp_path):
    """main() calls run_gap_query when --gap-query flag is present."""
    mod = _load()
    out_file = tmp_path / "gap.json"
    invoked = []

    def fake_gap(query, nb_id, out_path):
        invoked.append((query, nb_id, out_path))

    with patch.object(mod, "run_gap_query", side_effect=fake_gap), \
         patch("sys.argv", ["run_research.py",
                            "--gap-query", "EU sanctions list",
                            "--nb-id", "nb-999",
                            "--out", str(out_file)]):
        mod.main()

    assert len(invoked) == 1
    assert invoked[0] == ("EU sanctions list", "nb-999", str(out_file))


def test_main_workspace_mode_still_works(tmp_path):
    """main() still reads workspace queries and creates temp notebooks when no --gap-query."""
    mod = _load()
    state = {
        "nb_id": "main-nb-001",
        "scope": {"research_queries": [{"query_id": 1, "query": "OFAC SDN list"}]}
    }
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "state.json").write_text(__import__("json").dumps(state))

    calls = []
    def fake_run_cmd(cmd, check=True):
        calls.append(cmd)
        if "create" in cmd:
            return '{"id": "temp-nb-ws"}'
        if "research status" in cmd:
            return '{"status": "done"}'
        return ""

    with patch.object(mod, "run_cmd", side_effect=fake_run_cmd), \
         patch.object(mod, "time") as mock_time, \
         patch("sys.argv", ["run_research.py", str(ws)]):
        mock_time.sleep = lambda _: None
        mod.main()

    create_calls = [c for c in calls if "create" in c and "research-temp-q" in c]
    assert len(create_calls) == 1


def test_polling_timeout_is_at_least_40_minutes():
    """Guard against regressions to the original 5-min cap."""
    import ast
    src = SCRIPT.read_text()
    tree = ast.parse(src)
    caps = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for cmp, right in zip(node.ops, node.comparators):
                if isinstance(cmp, ast.Lt) and isinstance(right, ast.Constant):
                    caps.append(right.value)
    loop_caps = [c for c in caps if isinstance(c, int) and c >= 10]
    assert loop_caps, "No polling caps found in run_research.py"
    assert all(c >= 480 for c in loop_caps), (
        f"Polling cap(s) {loop_caps} are below 480 (40 min at 5s poll interval)"
    )
