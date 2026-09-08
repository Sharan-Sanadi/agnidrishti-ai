# AGNIDRISHTI API — Analysis Endpoint

import uuid
from datetime import datetime

from fastapi import APIRouter

from app.schemas.analysis import (
    AnalyzeRequest,
    HotspotAnalysis,
    IndustrialContext,
    LandCoverContext,
    SatelliteContext,
    TemporalContext,
    ThermalContext,
)
from app.schemas.classification import Classification
from app.schemas.common import DataQuality, DataSourceInfo, EvidenceItem
from app.schemas.hotspot import HotspotRead

router = APIRouter()

@router.post("", response_model=HotspotAnalysis)
def analyze_hotspot(request: AnalyzeRequest):
    """
    Analyze coordinates for thermal anomalies.
    Phase 0: Returns a SCAFFOLD/MOCK response to build the frontend against.
    DO NOT pretend this is a real AI prediction.
    """
    # Create a mock hotspot based on requested coords
    hotspot_id = str(uuid.uuid4())
    hotspot = HotspotRead(
        id=hotspot_id,
        latitude=request.latitude,
        longitude=request.longitude,
        acquired_at=datetime.utcnow(),
        source="NASA_FIRMS",
        confidence="nominal",
        frp_mw=25.5,
        brightness_ti4=310.2,
        brightness_ti5=292.1,
    )

    # Mock Contexts
    thermal = ThermalContext(
        frp_mw=hotspot.frp_mw,
        brightness_ti4=hotspot.brightness_ti4,
        brightness_ti5=hotspot.brightness_ti5,
        brightness_delta=18.1,
        day_night="D",
        detection_confidence="nominal"
    )
    temporal = TemporalContext(
        detection_count=5,
        persistence_score=0.72,
        frp_deviation=1.2
    )
    industrial = IndustrialContext(
        industrial_zone=True,
        industrial_facilities_500m=1,
        distance_to_nearest_m=350.5,
        infrastructure_types=["manufacturing"]
    )
    landcover = LandCoverContext(
        dominant_class="built_area",
        built_area_ratio=0.85,
        vegetation_ratio=0.10,
        source="ESA_WORLDCOVER"
    )
    satellite = SatelliteContext(
        has_recent_imagery=False
    )

    # Mock Classification
    classification = Classification(
        top_level_class="INDUSTRIAL",
        subclass="PROBABLE_INDUSTRIAL_FIRE",
        confidence=0.88,
        reasoning_summary="High persistence and close proximity to known manufacturing infrastructure suggest this is an industrial thermal source.",
        evidence=[
            EvidenceItem(
                type="industrial_proximity",
                label="Distance to infrastructure",
                value=350.5,
                unit="m",
                weight_or_importance=0.9
            ),
            EvidenceItem(
                type="temporal_persistence",
                label="Persistence Score",
                value=0.72,
                weight_or_importance=0.8
            )
        ],
        model_version="fixture-v0",
        requires_ground_verification=True
    )

    return HotspotAnalysis(
        hotspot=hotspot,
        thermal_context=thermal,
        temporal_context=temporal,
        industrial_context=industrial,
        landcover_context=landcover,
        satellite_context=satellite,
        classification=classification,
        anomaly_score=0.45,
        warnings=["This is a fixture mode response. Do not use for real analysis."],
        data_sources=[
            DataSourceInfo(source_name="NASA_FIRMS", source_version="v1"),
            DataSourceInfo(source_name="OPENSTREETMAP"),
        ],
        data_quality=DataQuality(overall_quality="medium"),
        analysis_mode="fixture"
    )
