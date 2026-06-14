"""Composition root.

Build singletons once at startup; FastAPI ``Depends`` returns references via the
``app.state`` slot so the same instances are shared across request handlers and
the background poller.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx
from fastapi import Request

from vambora.adapters.outbound.event_bus.inproc import InProcEventBus
from vambora.adapters.outbound.notifications.logging_notifier import LoggingNotifier
from vambora.adapters.outbound.persistence.repositories.alert_rules import (
    PostgresAlertRuleRepository,
)
from vambora.adapters.outbound.persistence.repositories.catalog import (
    PostgresCatalogRepository,
)
from vambora.adapters.outbound.persistence.repositories.predictions import (
    PostgresPredictionRepository,
)
from vambora.adapters.outbound.persistence.repositories.vehicle_positions import (
    PostgresVehiclePositionRepository,
)
from vambora.adapters.outbound.persistence.unit_of_work import Database
from vambora.adapters.outbound.providers.gtfs_loader import GtfsLoader
from vambora.adapters.outbound.providers.sppo_client import SppoClient
from vambora.adapters.outbound.routing.otp_client import OtpClient
from vambora.adapters.outbound.snapshots.local_store import LocalSnapshotStore
from vambora.application.commands.build_snapshot import BuildSnapshot
from vambora.application.commands.compact_tracking_data import CompactTrackingData
from vambora.application.commands.delete_alert_rule import DeleteAlertRule
from vambora.application.commands.evaluate_alerts import EvaluateAlerts
from vambora.application.commands.import_gtfs_catalog import ImportGtfsCatalog
from vambora.application.commands.ingest_vehicle_positions import IngestVehiclePositions
from vambora.application.commands.register_alert_rule import RegisterAlertRule
from vambora.application.queries.find_nearby_stops import FindNearbyStops
from vambora.application.queries.get_line_realtime import GetLineRealtime
from vambora.application.queries.get_line_shape import GetLineShape
from vambora.application.queries.get_line_stats import GetLineStats
from vambora.application.queries.get_live_vehicles import GetLiveVehicles
from vambora.application.queries.get_stop import GetStop
from vambora.application.queries.get_stop_arrivals import GetStopArrivals
from vambora.application.queries.get_stop_predictions import GetStopPredictions
from vambora.application.queries.get_vehicle_history import GetVehicleHistory
from vambora.application.queries.list_alert_rules import ListAlertRules
from vambora.application.queries.list_routes import ListRoutes
from vambora.application.queries.plan_trip import PlanTrip
from vambora.shared.config import Settings
from vambora.shared.time import SystemClock


@dataclass
class Container:
    settings: Settings
    db: Database
    http_client: httpx.AsyncClient
    vehicle_repository: PostgresVehiclePositionRepository
    catalog_repository: PostgresCatalogRepository
    sppo: SppoClient
    gtfs: GtfsLoader
    event_bus: InProcEventBus
    ingest: IngestVehiclePositions
    import_gtfs_catalog: ImportGtfsCatalog
    get_live_vehicles: GetLiveVehicles
    get_vehicle_history: GetVehicleHistory
    find_nearby_stops: FindNearbyStops
    list_routes: ListRoutes
    get_line_realtime: GetLineRealtime
    get_line_shape: GetLineShape
    get_line_stats: GetLineStats
    get_stop: GetStop
    get_stop_arrivals: GetStopArrivals
    get_stop_predictions: GetStopPredictions
    plan_trip: PlanTrip
    snapshot_store: LocalSnapshotStore
    build_snapshot: BuildSnapshot
    register_alert_rule: RegisterAlertRule
    delete_alert_rule: DeleteAlertRule
    list_alert_rules: ListAlertRules
    evaluate_alerts: EvaluateAlerts
    compact_tracking_data: CompactTrackingData


def build_container(settings: Settings) -> Container:
    db = Database(settings.database_url, null_pool=settings.db_null_pool)
    http_client = httpx.AsyncClient()
    vehicle_repository = PostgresVehiclePositionRepository(
        db, store_raw=settings.store_raw_payload
    )
    catalog_repository = PostgresCatalogRepository(db)
    prediction_repository = PostgresPredictionRepository(db)
    alert_rule_repository = PostgresAlertRuleRepository(db)
    notifier = LoggingNotifier()
    sppo = SppoClient(base_url=settings.sppo_url, http_client=http_client)
    gtfs = GtfsLoader(source_url=settings.gtfs_url, http_client=http_client)
    otp = OtpClient(base_url=settings.otp_url, http_client=http_client)
    snapshot_store = LocalSnapshotStore(Path(settings.snapshot_dir))
    event_bus = InProcEventBus()
    clock = SystemClock()
    ingest = IngestVehiclePositions(
        provider=sppo,
        repository=vehicle_repository,
        clock=clock,
        window_seconds=settings.sppo_window_seconds,
    )
    return Container(
        settings=settings,
        db=db,
        http_client=http_client,
        vehicle_repository=vehicle_repository,
        catalog_repository=catalog_repository,
        sppo=sppo,
        gtfs=gtfs,
        event_bus=event_bus,
        ingest=ingest,
        import_gtfs_catalog=ImportGtfsCatalog(provider=gtfs, repository=catalog_repository),
        get_live_vehicles=GetLiveVehicles(repository=vehicle_repository),
        get_vehicle_history=GetVehicleHistory(repository=vehicle_repository),
        find_nearby_stops=FindNearbyStops(repository=catalog_repository),
        list_routes=ListRoutes(repository=catalog_repository),
        get_line_realtime=GetLineRealtime(catalog=catalog_repository, tracking=vehicle_repository),
        get_line_shape=GetLineShape(repository=catalog_repository),
        get_line_stats=GetLineStats(repository=vehicle_repository),
        get_stop=GetStop(repository=catalog_repository),
        get_stop_arrivals=GetStopArrivals(repository=catalog_repository, settings=settings),
        get_stop_predictions=GetStopPredictions(
            repository=prediction_repository, settings=settings
        ),
        plan_trip=PlanTrip(engine=otp, settings=settings),
        snapshot_store=snapshot_store,
        build_snapshot=BuildSnapshot(
            repository=catalog_repository, store=snapshot_store, clock=clock
        ),
        register_alert_rule=RegisterAlertRule(
            rules=alert_rule_repository, catalog=catalog_repository
        ),
        delete_alert_rule=DeleteAlertRule(rules=alert_rule_repository),
        list_alert_rules=ListAlertRules(rules=alert_rule_repository),
        evaluate_alerts=EvaluateAlerts(
            rules=alert_rule_repository,
            predictions=prediction_repository,
            notifier=notifier,
            clock=clock,
            settings=settings,
        ),
        compact_tracking_data=CompactTrackingData(
            repository=vehicle_repository,
            clock=clock,
            timescale=settings.db_timescale,
            retention_hours=settings.retention_hours,
        ),
    )


def container(request: Request) -> Container:
    return request.app.state.container  # type: ignore[no-any-return]
