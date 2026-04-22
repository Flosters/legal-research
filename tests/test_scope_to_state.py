import json, sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent / "references/scripts"))
import scope_to_state as s2s

SCOPE_OK = {
  "topic": "Despido sin causa",
  "jurisdiction": "Argentina",
  "area_of_law": "Laboral",
  "posture": "litigation",
  "report_language": "es",
  "legally_relevant_date": "2023-08-15",
  "research_checklist": [
    {"node_id": 1, "name": "Rule on dismissal", "criterion": "2+ primary authorities"}
  ],
  "research_queries": [
    {"query_id": 1, "angle": "primary authority", "query": "...", "nodes": [1]}
  ]
}

def test_valid_scope_writes_workspace(tmp_path):
    out = s2s.build(tmp_path, SCOPE_OK)
    state = json.loads((out / "state.json").read_text())
    assert state["scope"]["topic"] == "Despido sin causa"
    assert state["research_checklist"][0]["node_id"] == 1
    assert "1" in state["completed_phases"]
    assert state["next_phase"] == "2"

def test_invalid_scope_rejected(tmp_path):
    bad = dict(SCOPE_OK, posture="banana")
    with pytest.raises(Exception):
        s2s.build(tmp_path, bad)

def test_slug_is_filesystem_safe(tmp_path):
    out = s2s.build(tmp_path, SCOPE_OK)
    assert "/" not in out.name and " " not in out.name
