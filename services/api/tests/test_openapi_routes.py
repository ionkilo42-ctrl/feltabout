import os
import sys
import warnings
from pathlib import Path

os.environ.setdefault("AI_PROVIDER", "local")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("ENCRYPTION_KEY", "nY1jcI7NI5vxhAXu7r_MT4h84trDxTcf6dzWTqtlSUU=")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


def test_openapi_operation_ids_are_unique():
    app.openapi_schema = None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        schema = app.openapi()

    operation_ids = [
        operation["operationId"]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if "operationId" in operation
    ]

    assert len(operation_ids) == len(set(operation_ids))
    duplicate_warnings = [
        warning for warning in caught if "Duplicate Operation ID" in str(warning.message)
    ]
    assert duplicate_warnings == []
