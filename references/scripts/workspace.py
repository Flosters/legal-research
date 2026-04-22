"""Workspace + state.json helper for the hybrid legal-research skill.

Called by the orchestrator and by every phase subagent. The state.json at
<workspace>/state.json is the single source of truth between subagents.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "state.schema.json"


def _validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMA_PATH.read_text()))


def init_workspace(root: Path, slug: str, scope: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = Path(root) / f"{slug}-{ts}"
    path.mkdir(parents=True, exist_ok=False)
    state = {
        "schema_version": 1,
        "slug": slug,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_phases": ["1"],
        "next_phase": "2",
        "scope": scope,
    }
    _validator().validate(state)
    (path / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2))
    return path


def load_state(workspace: Path) -> dict:
    return json.loads((Path(workspace) / "state.json").read_text())


def update_state(workspace: Path, patch: dict) -> dict:
    state = load_state(workspace)
    state.update(patch)
    _validator().validate(state)
    (Path(workspace) / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2))
    return state


def mark_phase_complete(workspace: Path, phase: str, next_phase: str) -> dict:
    state = load_state(workspace)
    if phase not in state["completed_phases"]:
        state["completed_phases"].append(phase)
    state["next_phase"] = next_phase
    _validator().validate(state)
    (Path(workspace) / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2))
    return state
