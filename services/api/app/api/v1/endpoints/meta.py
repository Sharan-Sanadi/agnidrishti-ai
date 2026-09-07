# AGNIDRISHTI API — Meta Endpoints

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/readiness")
def get_readiness() -> dict[str, bool]:
    """
    Return configuration/provider readiness without leaking secrets.
    Allows the frontend to know if the system is in degraded/fixture mode.
    """
    return {
        "database_configured": settings.is_database_configured,
        "firms_configured": settings.is_firms_configured,
        "earth_engine_configured": settings.is_earth_engine_configured,
        "supabase_configured": settings.is_supabase_configured,
    }
