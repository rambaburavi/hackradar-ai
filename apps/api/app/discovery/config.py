from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config import PROJECT_ROOT


class DiscoverySettings(BaseSettings):

    DISCOVERY_TIMEOUT_SECONDS: float = Field(
        default=10,
        gt=0,
        le=120,
    )

    DISCOVERY_MAX_RETRIES: int = Field(
        default=1,
        ge=0,
        le=5,
    )

    DISCOVERY_MAX_CONCURRENCY: int = Field(
        default=3,
        ge=1,
        le=10,
    )

    DISCOVERY_MAX_EVENTS_PER_SOURCE: int = Field(
        default=100,
        ge=1,
        le=500,
    )

    DISCOVERY_MAX_RESPONSE_BYTES: int = Field(
        default=5_000_000,
        ge=1024,
        le=20_000_000,
    )

    DISCOVERY_USER_AGENT: str = "HackRadarAI/0.1"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )


discovery_settings = DiscoverySettings()