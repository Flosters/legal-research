import pytest
import json
import tempfile
import subprocess
from pathlib import Path

def test_cross_check_citations():
    state_data = {
        "evidence_registry": [
            {"title": "Valid Primary", "tier": "T1", "queryable_status": "Queryable ✓"},
            {"title": "Secondary Source", "tier": "T2", "queryable_status": "Queryable ✓"},
            {"title": "Unqueryable Primary", "tier": "T1", "queryable_status": "NOT QUERYABLE — DISCLOSED"}
        ]
    }
    
    citation_log = """
Citation 1:
  Verified Against: Valid Primary
  Status: ✓ Verified
Citation 2:
  Verified Against: Secondary Source
  Status: ✓ Verified
Citation 3:
  Verified Against: Unqueryable Primary
  Status: ✓ Verified
"""
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as state_f, \
         tempfile.NamedTemporaryFile(mode="w", delete=False) as log_f:
        json.dump(state_data, state_f)
        log_f.write(citation_log)
        state_path, log_path = state_f.name, log_f.name
        
    script_path = Path("references/scripts/cross_check_citations.py")
    result = subprocess.run(["python3", str(script_path), state_path, log_path], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "[SECONDARY ONLY]" in result.stdout # Citation 2 and 3 should be downgraded
    
    Path(state_path).unlink()
    Path(log_path).unlink()
