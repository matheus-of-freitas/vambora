from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(alias="DATABASE_URL")
    database_url_sync: str = Field(alias="DATABASE_URL_SYNC")
    redis_url: str = Field(alias="REDIS_URL")

    sppo_url: str = Field(alias="SPPO_URL")
    sppo_poll_interval_seconds: int = Field(default=30, alias="SPPO_POLL_INTERVAL_SECONDS")
    sppo_window_seconds: int = Field(default=45, alias="SPPO_WINDOW_SECONDS")

    gtfs_url: str = Field(alias="GTFS_URL")
    gtfs_date_override: str | None = Field(default=None, alias="GTFS_DATE_OVERRIDE")

    otp_url: str = Field(default="http://localhost:8080", alias="OTP_URL")

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
