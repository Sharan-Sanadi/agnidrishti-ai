# AGNIDRISHTI API — Core Configuration
"""
Application settings using pydantic-settings.
The API boots without optional integration credentials.
Missing providers are marked 'unavailable' rather than crashing.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Application ───
    app_env: str = "development"
    app_name: str = "agnidrishti-api"
    app_version: str = "0.1.0"
    debug: bool = True

    # ─── Supabase / Database ───
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout_seconds: float = 30.0

    @property
    def async_database_url(self) -> str:
        """
        Normalize database URL for async SQLAlchemy.
        Ensures postgresql+asyncpg:// scheme is used.
        """
        url = (self.database_url or "").strip()
        if not url:
            return ""
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        return url

    @property
    def sanitized_database_url(self) -> str:
        """
        Return database URL with password redacted for safe logging.
        Never logs credentials.
        """
        url = self.async_database_url
        if not url:
            return "not_configured"
        try:
            from urllib.parse import urlsplit, urlunsplit
            parsed = urlsplit(url)
            if parsed.password:
                netloc = f"{parsed.username or ''}:***@{parsed.hostname or ''}"
                if parsed.port:
                    netloc += f":{parsed.port}"
                return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))
            return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
        except Exception:
            return "configured_redacted"

    # ─── NASA FIRMS ───
    firms_map_key: str = ""
    nasa_firms_map_key: str = ""
    nasa_firms_base_url: str = "https://firms.modaps.eosdis.nasa.gov"
    nasa_firms_default_day_range: int = 1
    nasa_firms_timeout_seconds: float = 20.0
    nasa_firms_cache_ttl_seconds: int = 600

    @property
    def effective_firms_map_key(self) -> str:
        """Resolve FIRMS map key from either NASA_FIRMS_MAP_KEY or FIRMS_MAP_KEY."""
        return (self.nasa_firms_map_key or self.firms_map_key).strip()

    # ─── Phase 3 Temporal Persistence ───
    persistence_radius_meters: float = 750.0
    persistence_lookback_days: int = 30
    persistence_min_history_days: int = 21
    persistence_algorithm_version: str = "temporal_persistence_v1"
    persistence_backfill_chunk_days: int = 5

    # ─── OSM / Overpass ───
    overpass_api_url: str = "https://overpass-api.de/api/interpreter"

    # ─── Phase 5 ESA WorldCover ───
    worldcover_base_url: str = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map"
    worldcover_year: int = 2021
    worldcover_version: str = "v200"
    worldcover_product_name: str = "ESA WorldCover 10 m 2021"
    worldcover_max_radius_m: float = 1000.0
    worldcover_timeout_seconds: float = 30.0
    worldcover_max_concurrency: int = 4
    worldcover_cache_dir: str = "data/cache/worldcover"
    worldcover_algorithm_version: str = "land_cover_v1"

    # ─── Phase 6 Sentinel-2 L2A (Copernicus Data Space Ecosystem) ───
    cdse_client_id: str = ""
    cdse_client_secret: str = ""
    cdse_token_url: str = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    cdse_sentinel_hub_base_url: str = "https://sh.dataspace.copernicus.eu"
    cdse_stac_base_url: str = "https://catalogue.dataspace.copernicus.eu/stac"
    sentinel_collection: str = "sentinel-2-l2a"
    sentinel_lookback_days: int = 30
    sentinel_max_candidates: int = 8
    sentinel_sync_batch_limit: int = 50
    sentinel_algorithm_version: str = "sentinel2_context_v1"
    sentinel_analytical_resolution_m: float = 20.0
    sentinel_timeout_seconds: float = 35.0

    # ─── Google Earth Engine ───
    gee_project_id: str = ""
    google_application_credentials: str = ""

    # ─── CORS ───
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ─── Provider readiness helpers ───
    @property
    def is_database_configured(self) -> bool:
        return bool(self.database_url)

    @property
    def is_firms_configured(self) -> bool:
        return bool(self.effective_firms_map_key)

    @property
    def is_cdse_configured(self) -> bool:
        return bool(self.cdse_client_id.strip() and self.cdse_client_secret.strip())

    @property
    def is_earth_engine_configured(self) -> bool:
        return bool(self.gee_project_id and self.google_application_credentials)

    @property
    def is_supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]



def get_settings() -> Settings:
    """Factory for application settings (cacheable in future)."""
    return Settings()
