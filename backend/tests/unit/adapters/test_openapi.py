from __future__ import annotations

import pytest

from vambora.adapters.inbound.http.app import create_app
from vambora.shared.config import Settings

pytestmark = pytest.mark.unit

# The web generates its typed client from this schema; if a router or DTO
# silently disappears the generated types drift. This guards the contract
# without a running server (FastAPI builds the schema from the route table).
_REQUIRED_PATHS = {
    "/health",
    "/vehicles",
    "/lines/{short_name}/realtime",
    "/stops/{stop_id}",
    "/stops/{stop_id}/arrivals",
    "/stops/{stop_id}/predictions",
    "/trips/plan",
    "/alerts/rules",
    "/alerts/rules/{rule_id}",
    "/snapshots/latest",
}
_REQUIRED_SCHEMAS = {
    "VehiclePositionDTO",
    "StopDTO",
    "ArrivalDTO",
    "PredictionDTO",
    "ItineraryDTO",
    "LegDTO",
    "ConnectionDTO",
    "AlertRuleDTO",
    "SnapshotLatestDTO",
}


def _schema() -> dict[str, object]:
    settings = Settings.model_construct(environment="local")
    app = create_app(settings)
    return app.openapi()


def test_openapi_is_31_and_has_core_contract() -> None:
    schema = _schema()
    assert str(schema["openapi"]).startswith("3.1")

    paths = set(schema["paths"])  # type: ignore[arg-type]
    missing = _REQUIRED_PATHS - paths
    assert not missing, f"missing OpenAPI paths: {sorted(missing)}"

    components = schema["components"]
    schemas = set(components["schemas"])  # type: ignore[index,arg-type]
    missing_schemas = _REQUIRED_SCHEMAS - schemas
    assert not missing_schemas, f"missing OpenAPI schemas: {sorted(missing_schemas)}"
