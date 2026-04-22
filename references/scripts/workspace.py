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


# ---- CLI entrypoint ----
def _cli():
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_mc = sub.add_parser("mark-complete")
    p_mc.add_argument("workspace"); p_mc.add_argument("phase"); p_mc.add_argument("next_phase")

    p_up = sub.add_parser("update")
    p_up.add_argument("workspace")
    p_up.add_argument("--set", dest="sets", action="append", default=[],
                      help="key=value; repeatable")
    p_up.add_argument("--mark-complete", dest="mark", default=None)
    p_up.add_argument("--next-phase", dest="next", default=None)

    args = ap.parse_args()
    w = Path(args.workspace)
    if args.cmd == "mark-complete":
        mark_phase_complete(w, args.phase, args.next_phase)
    elif args.cmd == "update":
        patch = {}
        for kv in args.sets:
            if "=" not in kv:
                raise SystemExit(f"bad --set: {kv}")
            k, v = kv.split("=", 1)
            patch[k] = v
        if patch:
            update_state(w, patch)
        if args.mark:
            if not args.next:
                raise SystemExit("--mark-complete requires --next-phase")
            mark_phase_complete(w, args.mark, args.next)

if __name__ == "__main__":
    _cli()
