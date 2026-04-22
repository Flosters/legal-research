import json, subprocess, sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "references/scripts/workspace.py"

def _init(tmp_path):
    scope = {"topic":"X","jurisdiction":"Argentina","report_language":"es"}
    import sys as _sys
    _sys.path.insert(0, str(SCRIPT.parent))
    import workspace as ws
    return ws.init_workspace(tmp_path, slug="x", scope=scope)

def test_mark_complete_cli(tmp_path):
    ws_path = _init(tmp_path)
    r = subprocess.run([sys.executable, str(SCRIPT), "mark-complete", str(ws_path), "2", "3"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    state = json.loads((ws_path / "state.json").read_text())
    assert "2" in state["completed_phases"]
    assert state["next_phase"] == "3"

def test_update_set_cli(tmp_path):
    ws_path = _init(tmp_path)
    r = subprocess.run([sys.executable, str(SCRIPT), "update", str(ws_path),
                        "--set", "nb_id=nb-xyz"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    state = json.loads((ws_path / "state.json").read_text())
    assert state["nb_id"] == "nb-xyz"

def test_update_invalid_rejected(tmp_path):
    ws_path = _init(tmp_path)
    r = subprocess.run([sys.executable, str(SCRIPT), "update", str(ws_path),
                        "--set", "next_phase=nope"],
                       capture_output=True, text=True)
    assert r.returncode != 0
