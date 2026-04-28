"""One-time permissions setup for the legal-research skill.

Run once after installing the skill, then restart Claude Code:

    python3 ~/.claude/skills/legal-research/setup.py

Adds bash permissions to ~/.claude/settings.json that allow the skill's
subagents to run without mid-workflow authorization prompts.
No absolute paths are written — all permissions use command-pattern rules.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

_override = os.environ.get("CLAUDE_SETTINGS_PATH")
SETTINGS = Path(_override) if _override else Path("~/.claude/settings.json").expanduser()

REQUIRED_PERMISSIONS = [
    "Bash(notebooklm *)",
    "Bash(python3 *)",
    "Bash(open *)",
    "Bash(jq *)",
    "Agent(*)",
]


def apply_permissions(settings_path: Path = SETTINGS) -> list[str]:
    """Add missing permissions to settings_path. Returns list of newly added entries."""
    data = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    allow: list[str] = data.setdefault("permissions", {}).setdefault("allow", [])
    added = [p for p in REQUIRED_PERMISSIONS if p not in allow]
    if added:
        allow.extend(added)
        settings_path.write_text(json.dumps(data, indent=2))
    return added


def is_configured(settings_path: Path = SETTINGS) -> bool:
    """Return True if all required permissions are already present."""
    if not settings_path.exists():
        return False
    allow = json.loads(settings_path.read_text()).get("permissions", {}).get("allow", [])
    return all(p in allow for p in REQUIRED_PERMISSIONS)


if __name__ == "__main__":
    if "--check" in sys.argv:
        if is_configured():
            print("Permissions OK.")
            sys.exit(0)
        else:
            print("ERROR: Run setup.py first, then restart Claude Code.")
            sys.exit(1)

    added = apply_permissions()
    if added:
        print(f"Permissions added: {added}")
        print("Restart Claude Code for the changes to take effect.")
    else:
        print("Already configured — no changes needed.")
