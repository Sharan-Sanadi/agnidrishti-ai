# AGNIDRISHTI API — Hotspots Endpoints

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.hotspot import HotspotListResponse, HotspotRead

router = APIRouter()

# Path to root: endpoints -> v1 -> api -> app -> api -> services -> root
FIXTURES_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent / "data" / "fixtures" / "hotspots.json"

def load_fixtures() -> list[dict]:
    if not FIXTURES_PATH.exists():
        return []
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        return json.load(f)

@router.get("", response_model=HotspotListResponse)
def get_hotspots():
    """
    Get recent thermal detections.
    Phase 0: Returns fixture data.
    """
    raw_data = load_fixtures()
    # Pydantic will validate and transform these dictionaries into HotspotRead instances.
    return HotspotListResponse(
        hotspots=raw_data,
        total=len(raw_data),
        analysis_mode="fixture"
    )

@router.get("/{hotspot_id}", response_model=HotspotRead)
def get_hotspot(hotspot_id: str):
    """
    Get a specific thermal detection.
    Phase 0: Looks up from fixture data.
    """
    raw_data = load_fixtures()
    for item in raw_data:
        if item.get("id") == hotspot_id:
            return item
    raise HTTPException(status_code=404, detail="Hotspot not found")
