import json
import tempfile
from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).parent.parent / "references/scripts/cross_check_citations.py"


def _run(state_data: dict, log_text: str, extra_args: list[str] = []) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as sf:
        json.dump(state_data, sf)
        state_path = sf.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as lf:
        lf.write(log_text)
        log_path = lf.name
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as of:
        out_path = of.name

    result = subprocess.run(
        [sys.executable, str(SCRIPT), state_path, log_path, out_path] + extra_args,
        capture_output=True, text=True
    )
    output_written = Path(out_path).read_text() if Path(out_path).exists() else ""
    for p in [state_path, log_path, out_path]:
        Path(p).unlink(missing_ok=True)
    result.output_written = output_written
    return result


def test_exits_zero_on_valid_input():
    state = {"evidence_registry": [
        {"title": "A", "url": "http://example.com/a", "import_status": "imported", "queryable_status": "queryable"},
    ]}
    r = _run(state, "http://example.com/a present in log")
    assert r.returncode == 0


def test_writes_report_file():
    state = {"evidence_registry": []}
    r = _run(state, "")
    assert "## Summary" in r.output_written


def test_flags_url_not_in_log():
    state = {"evidence_registry": [
        {"title": "Missing", "url": "http://missing.example.com", "import_status": "imported", "queryable_status": "queryable"},
    ]}
    r = _run(state, "some other content with no matching url")
    assert "[UNVERIFIED]" in r.output_written
    assert "Missing" in r.output_written


def test_flags_invalid_import_status():
    state = {"evidence_registry": [
        {"title": "Bad", "url": "http://x.com", "import_status": "UNKNOWN_STATUS", "queryable_status": "queryable"},
    ]}
    r = _run(state, "http://x.com")
    assert "import_status" in r.output_written
    assert "UNKNOWN_STATUS" in r.output_written


def test_flags_invalid_queryable_status():
    state = {"evidence_registry": [
        {"title": "Bad", "url": "http://x.com", "import_status": "imported", "queryable_status": "Queryable ✓"},
    ]}
    r = _run(state, "http://x.com")
    assert "queryable_status" in r.output_written


def test_summary_counts_are_correct():
    state = {"evidence_registry": [
        {"title": "A", "url": "http://a.com", "import_status": "imported", "queryable_status": "queryable"},
        {"title": "B", "url": "http://b.com", "import_status": "imported", "queryable_status": "queryable"},
    ]}
    r = _run(state, "http://a.com")
    assert "Registry entries: 2" in r.output_written
    assert "Unverified: 1" in r.output_written


def test_handles_missing_output_arg_gracefully():
    """When called with only 2 args, output goes to state_path.parent/final_citation_log.txt."""
    import tempfile, os
    with tempfile.TemporaryDirectory() as d:
        state_path = Path(d) / "state.json"
        log_path = Path(d) / "citations.txt"
        state_path.write_text(json.dumps({"evidence_registry": []}))
        log_path.write_text("")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(state_path), str(log_path)],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert (Path(d) / "final_citation_log.txt").exists()


def test_evidence_registry_as_json_string():
    """state.json may store evidence_registry as a JSON string (workspace.py --set serializes it)."""
    registry = [{"title": "A", "url": "http://a.com", "import_status": "imported", "queryable_status": "queryable"}]
    state = {"evidence_registry": json.dumps(registry)}
    r = _run(state, "http://a.com")
    assert r.returncode == 0
    assert "Registry entries: 1" in r.output_written
