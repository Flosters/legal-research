import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "references/scripts/check_urls.py"


def _run(urls: list[str], extra_args: list[str] = []) -> tuple[subprocess.CompletedProcess, dict]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("\n".join(urls))
        urls_path = f.name
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out_path = f.name

    result = subprocess.run(
        [sys.executable, str(SCRIPT), urls_path, "--output", out_path] + extra_args,
        capture_output=True, text=True
    )
    data = json.loads(Path(out_path).read_text()) if Path(out_path).exists() else []
    Path(urls_path).unlink(missing_ok=True)
    Path(out_path).unlink(missing_ok=True)
    return result, data


def test_exits_zero_always():
    r, _ = _run(["http://definitely-does-not-exist-zzz.invalid"])
    assert r.returncode == 0


def test_empty_file_produces_empty_results():
    r, data = _run([])
    assert data == []


def test_skips_comment_lines():
    r, data = _run(["# this is a comment", "http://also-invalid.invalid"])
    assert len(data) == 1
    assert data[0]["url"] == "http://also-invalid.invalid"


def test_unreachable_url_marked_not_ok():
    r, data = _run(["http://definitely-does-not-exist-zzz.invalid"], ["--timeout", "2"])
    assert len(data) == 1
    assert data[0]["ok"] is False
    assert data[0]["url"] == "http://definitely-does-not-exist-zzz.invalid"


def test_result_has_required_fields():
    r, data = _run(["http://definitely-does-not-exist-zzz.invalid"], ["--timeout", "2"])
    assert "url" in data[0]
    assert "ok" in data[0]
    assert "status" in data[0]


def test_output_written_to_specified_path():
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("http://definitely-does-not-exist-zzz.invalid\n")
        urls_path = f.name
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        custom_out = f.name

    subprocess.run(
        [sys.executable, str(SCRIPT), urls_path, "--output", custom_out, "--timeout", "2"],
        capture_output=True
    )
    assert Path(custom_out).exists()
    data = json.loads(Path(custom_out).read_text())
    assert isinstance(data, list)
    Path(urls_path).unlink(missing_ok=True)
    Path(custom_out).unlink(missing_ok=True)


import importlib.util
from unittest.mock import patch


def test_ssl_context_uses_certifi(tmp_path):
    """check_url() must pass certifi's cafile to ssl.create_default_context."""
    import certifi
    import ssl

    cafile_used = []
    original = ssl.create_default_context

    def capturing_create(**kwargs):
        cafile_used.append(kwargs.get("cafile"))
        ctx = original(**kwargs)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    spec = importlib.util.spec_from_file_location("check_urls_mod", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)

    with patch("ssl.create_default_context", side_effect=capturing_create):
        spec.loader.exec_module(mod)
        try:
            mod.check_url("https://httpbin.org/status/200", timeout=1)
        except Exception:
            pass  # network may be blocked in CI — we only care about the call

    assert cafile_used, "ssl.create_default_context was never called"
    assert cafile_used[0] == certifi.where(), (
        f"Expected cafile={certifi.where()!r}, got {cafile_used[0]!r}"
    )
