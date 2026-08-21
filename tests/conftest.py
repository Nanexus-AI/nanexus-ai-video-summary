from __future__ import annotations
import json
from pathlib import Path
import pytest
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "migration-baseline.v1.json"
@pytest.fixture(scope="session")
def migration_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
