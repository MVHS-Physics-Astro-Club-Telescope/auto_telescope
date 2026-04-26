"""Pydantic-settings driven runtime configuration.

All knobs read from environment variables prefixed with ``AUTO_TELESCOPE_``.
This is the single source of truth for runtime config — no hardcoded paths
or magic numbers anywhere else in the codebase.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from auto_telescope.config.site import MVHS_SITE, Site


class Settings(BaseSettings):
    """Runtime settings, populated from env vars + defaults."""

    model_config = SettingsConfigDict(
        env_prefix="AUTO_TELESCOPE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Site location (override per-deployment) -------------------------------------------
    site_name: str = Field(default=MVHS_SITE.name)
    latitude: float = Field(default=MVHS_SITE.latitude, ge=-90.0, le=90.0)
    longitude: float = Field(default=MVHS_SITE.longitude, ge=-180.0, le=180.0)
    elevation_m: float = Field(default=MVHS_SITE.elevation_m, ge=-500.0, le=9000.0)
    timezone: str = Field(default=MVHS_SITE.timezone)

    # --- Conditions / API behavior ---------------------------------------------------------
    cache_dir: Path = Field(default=Path.home() / ".auto_telescope_cache")
    cache_ttl_seconds: int = Field(default=900, ge=0)  # 15 min
    api_timeout_seconds: float = Field(default=10.0, gt=0.0)
    api_user_agent: str = Field(default="auto-telescope/0.1 (mvhsphysicsastroclub@gmail.com)")

    # --- Safety thresholds (hard interlocks) -----------------------------------------------
    sun_avoidance_deg: float = Field(default=30.0, ge=0.0, le=90.0)
    min_altitude_deg: float = Field(default=20.0, ge=0.0, le=90.0)
    max_wind_speed_mps: float = Field(default=15.0, ge=0.0)

    # --- Visibility scoring ----------------------------------------------------------------
    min_observation_minutes: int = Field(default=30, ge=1)

    def to_site(self) -> Site:
        """Build a Site from the current settings (so env-var overrides take effect)."""
        return Site(
            name=self.site_name,
            latitude=self.latitude,
            longitude=self.longitude,
            elevation_m=self.elevation_m,
            timezone=self.timezone,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings instance.

    Cached so env vars only load once per process. Tests that change env vars must call
    ``get_settings.cache_clear()``.
    """
    return Settings()
