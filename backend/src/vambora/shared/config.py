from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(alias="DATABASE_URL")
    # Sync URL is only needed where Alembic runs (local dev, CI deploy job);
    # the Lambda runtime gets by with the async URL alone.
    database_url_sync: str = Field(default="", alias="DATABASE_URL_SYNC")
    # Not used by the current ingestion path (event bus is in-process) and
    # absent entirely in the serverless deployment.
    redis_url: str = Field(default="", alias="REDIS_URL")

    # True when the database has TimescaleDB (local docker-compose). False on
    # plain Postgres+PostGIS (Supabase free tier): migrations skip
    # hypertable/cagg DDL and CompactTrackingData takes over rollup+retention.
    db_timescale: bool = Field(default=True, alias="DB_TIMESCALE")
    # Use NullPool — required on Lambda, where frozen sandboxes hold pooled
    # sockets across invocations and resume with them half-closed.
    db_null_pool: bool = Field(default=False, alias="DB_NULL_POOL")
    # Persist the raw SPPO payload alongside parsed columns. Disable in prod:
    # it is the single biggest size lever against a 500 MB free Postgres.
    store_raw_payload: bool = Field(default=True, alias="STORE_RAW_PAYLOAD")
    # Raw vehicle_positions rows older than this are purged by
    # CompactTrackingData (no-op when db_timescale, where the retention
    # policy owns it).
    retention_hours: int = Field(default=24, alias="RETENTION_HOURS")

    sppo_url: str = Field(alias="SPPO_URL")
    sppo_poll_interval_seconds: int = Field(default=30, alias="SPPO_POLL_INTERVAL_SECONDS")
    sppo_window_seconds: int = Field(default=45, alias="SPPO_WINDOW_SECONDS")

    gtfs_url: str = Field(alias="GTFS_URL")
    gtfs_date_override: str | None = Field(default=None, alias="GTFS_DATE_OVERRIDE")

    otp_url: str = Field(default="http://localhost:8080", alias="OTP_URL")
    # Routing depends on OpenTripPlanner, which isn't deployed in the
    # serverless setup. When false, POST /trips/plan returns 503 instead of
    # failing against an unreachable OTP.
    routing_enabled: bool = Field(default=True, alias="ROUTING_ENABLED")

    # How many SPPO polls one poller invocation performs. The scheduled
    # Lambda fires once a minute; one poll per invocation keeps it inside the
    # Lambda free tier (sleeping for a second poll would bill the idle time).
    polls_per_invocation: int = Field(default=1, alias="POLLS_PER_INVOCATION")

    # Shared secret required on /admin/* when environment != "local". Empty
    # means admin endpoints are disabled (503) in non-local environments.
    admin_token: str = Field(default="", alias="ADMIN_TOKEN")

    # A transfer with less slack than this is flagged "apertada" (tight) in
    # the planner. Rio's GTFS has no transfers.txt, so this derived slack is
    # the honest connection-reliability signal (see plan.md Appendix: OTP).
    routing_tight_transfer_seconds: int = Field(
        default=180, alias="ROUTING_TIGHT_TRANSFER_SECONDS"
    )

    # Naive ETA tuning (plan.md decision #7). fresh_seconds gates vehicle
    # liveness on received_at; fallback floors the speed so a stopped bus
    # still yields a finite ETA; snap is how far a vehicle may sit off a
    # route shape to count as "on" it.
    eta_fresh_seconds: int = Field(default=180, alias="ETA_FRESH_SECONDS")
    eta_fallback_kmh: float = Field(default=15.0, alias="ETA_FALLBACK_KMH")
    eta_max_horizon_seconds: int = Field(default=3600, alias="ETA_MAX_HORIZON_SECONDS")
    eta_max_snap_m: float = Field(default=150.0, alias="ETA_MAX_SNAP_M")

    # Where built offline bundles land. Local FS for dev (gitignored);
    # an R2 store is the deferred, credential-gated swap.
    snapshot_dir: str = Field(default="snapshots", alias="SNAPSHOT_DIR")

    # Alert evaluation (plan.md decision #4). The evaluator loop runs every
    # interval; cooldown stops a rule re-firing while a bus dwells within
    # threshold. Reuses the ETA_* tuning for the prediction query.
    alert_eval_interval_seconds: int = Field(default=30, alias="ALERT_EVAL_INTERVAL_SECONDS")
    alert_cooldown_seconds: int = Field(default=600, alias="ALERT_COOLDOWN_SECONDS")

    http_host: str = Field(default="0.0.0.0", alias="HTTP_HOST")
    http_port: int = Field(default=8000, alias="HTTP_PORT")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    environment: str = Field(default="local", alias="ENVIRONMENT")

    # Comma-separated browser origins allowed via CORS when ENVIRONMENT is not
    # "local" (local uses "*"). Lets a deployed web app (e.g. a Cloudflare
    # Pages *.pages.dev URL) reach the API without owning a domain or editing
    # code — see plan.md "Appendix: Deployment (domain-deferred)".
    cors_allow_origins: str = Field(default="", alias="CORS_ALLOW_ORIGINS")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


def load_settings() -> Settings:
    return Settings()
