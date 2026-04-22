import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMA = Path(__file__).parent.parent / "references/schemas/state.schema.json"
FIXT = Path(__file__).parent / "fixtures"

@pytest.fixture(scope="module")
def validator():
    return Draft202012Validator(json.loads(SCHEMA.read_text()))

def test_schema_file_exists():
    assert SCHEMA.exists(), "state.schema.json missing"

def test_minimal_state_valid(validator):
    data = json.loads((FIXT / "state-valid-minimal.json").read_text())
    validator.validate(data)

def test_complete_state_valid(validator):
    data = json.loads((FIXT / "state-valid-complete.json").read_text())
    validator.validate(data)

def test_missing_scope_rejected(validator):
    data = json.loads((FIXT / "state-invalid-missing-scope.json").read_text())
    with pytest.raises(ValidationError):
        validator.validate(data)

def test_schema_requires_next_phase(validator):
    assert "next_phase" in validator.schema["required"]

def test_next_phase_enum_covers_all_phases(validator):
    props = validator.schema["properties"]["next_phase"]["enum"]
    assert set(["1","2","3","3.5","3.6","3.7","4","4.1","4.5","5","5.5","5.6","6","done"]).issubset(props)
