import pytest
import json
import tempfile
from pathlib import Path
import subprocess

def test_curate_sources():
    input_data = {
        "tasks": [
            {
                "query": "test query",
                "sources": [
                    {"title": "Test Title 1", "url": "https://gov.ar/1", "result_type": 1},
                    {"title": "Test Title 1", "url": "https://org.ar/1", "result_type": 1}, # Should be dropped (lower domain quality)
                    {"title": "Missing URL", "result_type": 1}, # Should be dropped
                ]
            }
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(input_data, f)
        temp_path = f.name
    
    script_path = Path("references/scripts/curate_sources.py")
    result = subprocess.run(["python3", str(script_path), temp_path], capture_output=True, text=True)
    
    # Expect failure until script is implemented
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert len(output) == 1
    assert output[0]["url"] == "https://gov.ar/1"
    
    Path(temp_path).unlink()
