# tests/test_dispatch_dry_run.py
"""
Smoke-test the orchestrator's dispatch flow without touching real notebooklm.
Verifies state.json progresses through every phase transition. Does NOT
dispatch real Claude subagents — it calls workspace.py mark-complete directly
to simulate each subagent's completion.
"""
import os, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
MOCK = Path(__file__).parent / "mock_notebooklm"
WS_PY = ROOT / "references/scripts/workspace.py"

def _run(cmd, **kw):
    kw.setdefault("check", True)
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    return subprocess.run(cmd, **kw)

def test_dispatch_progression(tmp_path):
    env = os.environ.copy()
    env["PATH"] = f"{MOCK}:{env['PATH']}"

    sys.path.insert(0, str(WS_PY.parent))
    import workspace as ws
    wsp = ws.init_workspace(tmp_path, slug="smoke", scope={
        "topic":"Despido","jurisdiction":"Argentina",
        "posture":"litigation","report_language":"es",
        "legally_relevant_date":"2023-08-15","area_of_law":"Laboral"
    })
    ws.update_state(wsp, {"nb_id":"nb-mock-1"})

    transitions = [("2","3"),("3.6","3.7"),("3.7","4"),
                   ("4.5","5"),("5","5.5"),("5.5","5.6"),("5.6","6"),("6","done")]
    for done_phase, next_phase in transitions:
        _run([sys.executable, str(WS_PY), "mark-complete", str(wsp), done_phase, next_phase])

    state = json.loads((wsp / "state.json").read_text())
    assert state["next_phase"] == "done"
    for p in ("2","3.6","3.7","4.5","5","5.5","5.6","6"):
        assert p in state["completed_phases"]
