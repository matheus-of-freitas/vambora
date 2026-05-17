from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(alias="DATABASE_URL")
    sppo_url: str = Field(alias="SPPO_URL")
    poll_interval_seconds: int = Field(default=30, alias="POLL_INTERVAL_SECONDS")
    window_seconds: int = Field(default=45, alias="WINDOW_SECONDS")
    http_host: str = Field(default="0.0.0.0", alias="HTTP_HOST")
    http_port: int = Field(default=8000, alias="HTTP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


settings = Settings()  # type: ignore[call-arg]
