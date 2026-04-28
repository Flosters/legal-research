import json
import sys
import tempfile
from pathlib import Path
import importlib.util

SETUP = Path(__file__).parent.parent / "setup.py"

REQUIRED_PERMISSIONS = [
    "Bash(notebooklm *)",
    "Bash(python3 *)",
    "Bash(open *)",
    "Bash(jq *)",
    "Agent(*)",
]


def _load_setup():
    spec = importlib.util.spec_from_file_location("setup", SETUP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_setup_exists():
    assert SETUP.exists(), "setup.py not found"


def test_adds_all_required_permissions():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({}, f)
        settings_path = Path(f.name)

    mod = _load_setup()
    mod.apply_permissions(settings_path)

    data = json.loads(settings_path.read_text())
    allow = data.get("permissions", {}).get("allow", [])
    missing = [p for p in REQUIRED_PERMISSIONS if p not in allow]
    assert not missing, f"Missing permissions: {missing}"
    settings_path.unlink()


def test_idempotent():
    """Running setup twice does not duplicate entries."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({}, f)
        settings_path = Path(f.name)

    mod = _load_setup()
    mod.apply_permissions(settings_path)
    mod.apply_permissions(settings_path)

    data = json.loads(settings_path.read_text())
    allow = data.get("permissions", {}).get("allow", [])
    for perm in REQUIRED_PERMISSIONS:
        assert allow.count(perm) == 1, f"Duplicate entry: {perm}"
    settings_path.unlink()


def test_preserves_existing_permissions():
    existing = {"permissions": {"allow": ["Bash(git *)", "Bash(npm *)"]}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(existing, f)
        settings_path = Path(f.name)

    mod = _load_setup()
    mod.apply_permissions(settings_path)

    data = json.loads(settings_path.read_text())
    allow = data.get("permissions", {}).get("allow", [])
    assert "Bash(git *)" in allow
    assert "Bash(npm *)" in allow
    settings_path.unlink()


def test_no_hardcoded_absolute_paths_in_file():
    """setup.py must not contain hardcoded /Users/... or /home/... paths."""
    content = SETUP.read_text()
    assert "/Users/" not in content, "Hardcoded /Users/ path found in setup.py"
    assert "/home/" not in content, "Hardcoded /home/ path found in setup.py"


def test_returns_added_count():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({}, f)
        settings_path = Path(f.name)

    mod = _load_setup()
    added = mod.apply_permissions(settings_path)
    assert isinstance(added, list)
    assert len(added) == len(REQUIRED_PERMISSIONS)
    settings_path.unlink()


def test_returns_empty_when_already_configured():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({}, f)
        settings_path = Path(f.name)

    mod = _load_setup()
    mod.apply_permissions(settings_path)
    added_second = mod.apply_permissions(settings_path)
    assert added_second == []
    settings_path.unlink()


def test_check_flag_exits_1_when_not_configured():
    import subprocess, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({}, f)
        settings_path = Path(f.name)

    result = subprocess.run(
        [sys.executable, str(SETUP), "--check"],
        capture_output=True, text=True,
        env={**os.environ, "CLAUDE_SETTINGS_PATH": str(settings_path)}
    )
    assert result.returncode == 1
    settings_path.unlink()
