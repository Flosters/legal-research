# tests/test_live_smoke.py
import os, subprocess, sys, time
from pathlib import Path
import pytest

pytestmark = pytest.mark.live

ROOT = Path(__file__).parent.parent

@pytest.mark.skipif(not os.environ.get("RUN_LIVE_SMOKE"),
                    reason="set RUN_LIVE_SMOKE=1 to enable")
def test_end_to_end_hybrid(tmp_path):
    """
    Run the hybrid skill end-to-end on a cheap canned question.

    Prereqs:
      - notebooklm CLI authenticated (run: notebooklm status)
      - claude CLI installed; this test shells out `claude -p` with the
        hybrid skill and a deterministic scoped query.
    """
    query = (
        "Investigá en Argentina la regla sobre preaviso en el despido sin causa del "
        "trabajador contratado por tiempo indeterminado, citando Ley 20.744 arts. 231-233."
    )
    out = subprocess.run(
        ["claude", "-p",
         f"/notebooklm-legal-research-hybrid new {query}",
         "--output-dir", str(tmp_path)],
        capture_output=True, text=True, timeout=60 * 90)
    assert out.returncode == 0, out.stderr[-2000:]

    report = list(tmp_path.glob("legal-research-*.html"))
    assert len(report) == 1, "exactly one HTML report expected"
    html = report[0].read_text()
    assert "LEGAL RESEARCH MEMORANDUM" in html or "INVESTIGACIÓN" in html
    assert "Ley 20.744" in html  # verbatim primary citation survived
    assert "Verification Notes" in html or "Notas de verificación" in html
