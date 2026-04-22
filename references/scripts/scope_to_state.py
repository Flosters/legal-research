"""Build a workspace from a scope dict produced by the orchestrator in Phase 1."""
from __future__ import annotations
import re, sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import workspace as ws

def _slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:60] or "session"

def build(root: Path, scope: dict) -> Path:
    slug = _slugify(scope["topic"])
    path = ws.init_workspace(root, slug=slug, scope={
        "topic":                 scope["topic"],
        "jurisdiction":          scope["jurisdiction"],
        "area_of_law":           scope.get("area_of_law",""),
        "posture":               scope["posture"],
        "report_language":       scope["report_language"],
        "legally_relevant_date": scope.get("legally_relevant_date",""),
    })
    patch = {}
    if "research_checklist" in scope:
        patch["research_checklist"] = scope["research_checklist"]
    if "research_queries" in scope:
        patch["research_queries"] = scope["research_queries"]
    if patch:
        ws.update_state(path, patch)
    return path

if __name__ == "__main__":
    root = Path(sys.argv[1])
    scope = json.loads(Path(sys.argv[2]).read_text())
    print(build(root, scope))
