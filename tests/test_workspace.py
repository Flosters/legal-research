import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "references/scripts"))
import workspace as ws

def test_init_creates_workspace_dir_and_state(tmp_path):
    scope = {"topic":"Despido","jurisdiction":"Argentina","report_language":"es"}
    path = ws.init_workspace(tmp_path, slug="despido-arg", scope=scope)
    assert path.exists()
    state = json.loads((path / "state.json").read_text())
    assert state["scope"]["topic"] == "Despido"
    assert state["next_phase"] == "2"
    assert "1" in state["completed_phases"]

def test_update_state_preserves_unrelated_keys(tmp_path):
    scope = {"topic":"X","jurisdiction":"Y","report_language":"es"}
    path = ws.init_workspace(tmp_path, slug="x", scope=scope)
    ws.update_state(path, {"nb_id": "nb-123", "next_phase": "3"})
    state = ws.load_state(path)
    assert state["nb_id"] == "nb-123"
    assert state["scope"]["topic"] == "X"
    assert "1" in state["completed_phases"]

def test_mark_phase_complete_advances_next_phase(tmp_path):
    scope = {"topic":"X","jurisdiction":"Y","report_language":"es"}
    path = ws.init_workspace(tmp_path, slug="x", scope=scope)
    ws.mark_phase_complete(path, phase="2", next_phase="3")
    state = ws.load_state(path)
    assert "2" in state["completed_phases"]
    assert state["next_phase"] == "3"

def test_update_state_rejects_schema_violation(tmp_path):
    scope = {"topic":"X","jurisdiction":"Y","report_language":"es"}
    path = ws.init_workspace(tmp_path, slug="x", scope=scope)
    with pytest.raises(Exception):
        ws.update_state(path, {"next_phase": "bogus-phase-name"})
