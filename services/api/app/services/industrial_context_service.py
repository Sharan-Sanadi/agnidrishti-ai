# AGNIDRISHTI API — Industrial Context Intelligence Service
from __future__ import annotations

import math
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.industrial_context_profile import IndustrialContextProfileModel
from app.db.models.osm_context_coverage import OSMContextCoverageModel
from app.db.models.osm_industrial_feature import OSMIndustrialFeatureModel
from app.db.models.thermal_observation import ThermalObservationModel
from app.providers.overpass import OverpassClient, classify_osm_taxonomy, normalize_osm_geometry
from app.schemas.industrial import (
    ContextClass,
    CoverageStatus,
    IndustrialContextProfileDTO,
    NearestFeatureDTO,
)

DEFAULT_INDUSTRIAL_RADIUS_M = 5000.0


def calculate_bounding_box(lat: float, lon: float, radius_m: float = 5000.0) -> tuple[float, float, float, float]:
    """
    Calculate geographically accurate bounding box (south, west, north, east) around point.
    Uses latitude-dependent longitude scaling.
    """
    lat_delta = radius_m / 111000.0
    lon_delta = radius_m / (111000.0 * max(math.cos(math.radians(lat)), 0.01))

    south = max(-90.0, lat - lat_delta)
    north = min(90.0, lat + lat_delta)
    west = max(-180.0, lon - lon_delta)
    east = min(180.0, lon + lon_delta)

    return south, west, north, east


class IndustrialContextService:
    """
    Core spatial intelligence service for Phase 4 Industrial Context.
    Computes metric distance, spatial containment, context strength, and full 5km envelope coverage.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def analyze_batch(
        self, observation_ids: list[str], radius_m: float = DEFAULT_INDUSTRIAL_RADIUS_M
    ) -> list[IndustrialContextProfileDTO]:
        """Analyze a list of observation IDs efficiently."""
        profiles = []
        for obs_id in observation_ids:
            p = await self.get_or_compute_profile(obs_id, radius_m)
            profiles.append(p)
        return profiles

    async def check_envelope_coverage(
        self, lat: float, lon: float, radius_m: float = DEFAULT_INDUSTRIAL_RADIUS_M
    ) -> tuple[CoverageStatus, datetime | None]:
        """
        Verify if the FULL 5km bounding envelope around (lat, lon) is completely covered
        by fresh active OSM coverage (expires_at > NOW()).

        Returns (CoverageStatus, osm_snapshot_at).
        """
        req_south, req_west, req_north, req_east = calculate_bounding_box(lat, lon, radius_m)
        now_utc = datetime.now(UTC)

        stmt = (
            select(
                OSMContextCoverageModel.completed_at,
                OSMContextCoverageModel.requested_at,
                func.ST_XMin(OSMContextCoverageModel.bbox_geom).label("west"),
                func.ST_YMin(OSMContextCoverageModel.bbox_geom).label("south"),
                func.ST_XMax(OSMContextCoverageModel.bbox_geom).label("east"),
                func.ST_YMax(OSMContextCoverageModel.bbox_geom).label("north"),
            )
            .where(
                OSMContextCoverageModel.status == "COMPLETE",
                OSMContextCoverageModel.expires_at > now_utc,
            )
            .order_by(OSMContextCoverageModel.completed_at.desc())
        )
        result = await self.db.execute(stmt)
        rows = result.fetchall()

        # 1. Full envelope containment -> ADEQUATE
        for row in rows:
            if row.west <= req_west and row.east >= req_east and row.south <= req_south and row.north >= req_north:
                return "ADEQUATE", row.completed_at or row.requested_at

        # 2. Observation point inside coverage -> PARTIAL
        for row in rows:
            if row.west <= lon <= row.east and row.south <= lat <= row.north:
                return "PARTIAL", row.completed_at or row.requested_at

        return "MISSING", None

    async def sync_osm_bbox(
        self, south: float, west: float, north: float, east: float, force_refresh: bool = False
    ) -> OSMContextCoverageModel:
        """
        Server-side Overpass sync for a bounded BBox region.
        Ingests features into osm_industrial_features and updates osm_context_coverage.
        """
        query_hash = f"{south:.4f}_{west:.4f}_{north:.4f}_{east:.4f}"
        now_utc = datetime.now(UTC)

        # Check existing fresh coverage unless force_refresh
        if not force_refresh:
            existing_stmt = select(OSMContextCoverageModel).where(
                OSMContextCoverageModel.query_hash == query_hash,
                OSMContextCoverageModel.status == "COMPLETE",
                OSMContextCoverageModel.expires_at > now_utc,
            )
            res = await self.db.execute(existing_stmt)
            existing = res.scalar_one_or_none()
            if existing:
                logger.info(f"Reusing existing fresh OSM coverage record: {existing.coverage_id}")
                return existing

        coverage_id = f"osm_cov_{query_hash}_{int(now_utc.timestamp())}"
        bbox_wkt = f"POLYGON(({west} {south}, {east} {south}, {east} {north}, {west} {north}, {west} {south}))"

        coverage_rec = OSMContextCoverageModel(
            coverage_id=coverage_id,
            query_hash=query_hash,
            bbox_geom=func.ST_GeomFromText(bbox_wkt, 4326),
            requested_at=now_utc,
            status="RUNNING",
            feature_count=0,
            expires_at=datetime.fromtimestamp(now_utc.timestamp() + 7 * 86400, tz=UTC),
        )
        self.db.add(coverage_rec)
        await self.db.flush()

        client = OverpassClient()
        try:
            elements = await client.fetch_industrial_features(south, west, north, east)
            ingested_count = 0

            for elem in elements:
                elem_type = elem.get("type", "node")
                elem_id = elem.get("id")
                if not elem_id:
                    continue

                osm_uid = f"{elem_type}/{elem_id}"
                tags = elem.get("tags", {})
                category, thermal_relevance = classify_osm_taxonomy(tags)
                try:
                    wkt_str, geom_quality, _ = normalize_osm_geometry(elem)
                    if not wkt_str:
                        continue
                except Exception as geom_err:
                    logger.debug(f"Failed to normalize geometry for {osm_uid}: {geom_err}")
                    continue

                # Upsert into osm_industrial_features
                existing_feat_stmt = select(OSMIndustrialFeatureModel).where(
                    OSMIndustrialFeatureModel.osm_uid == osm_uid
                )
                feat_res = await self.db.execute(existing_feat_stmt)
                existing_feat = feat_res.scalar_one_or_none()

                if existing_feat:
                    existing_feat.name = tags.get("name")
                    existing_feat.operator = tags.get("operator")
                    existing_feat.feature_category = category
                    existing_feat.thermal_relevance = thermal_relevance
                    existing_feat.industrial_tag = tags.get("industrial")
                    existing_feat.man_made_tag = tags.get("man_made")
                    existing_feat.power_tag = tags.get("power")
                    existing_feat.plant_source = tags.get("plant:source") or tags.get("generator:source")
                    existing_feat.landuse = tags.get("landuse")
                    existing_feat.tags = tags
                    existing_feat.geom = func.ST_GeomFromText(wkt_str, 4326)
                    existing_feat.geometry_quality = geom_quality
                    existing_feat.last_refreshed_at = now_utc
                else:
                    new_feat = OSMIndustrialFeatureModel(
                        osm_uid=osm_uid,
                        osm_type=elem_type,
                        osm_id=elem_id,
                        name=tags.get("name"),
                        operator=tags.get("operator"),
                        feature_category=category,
                        thermal_relevance=thermal_relevance,
                        industrial_tag=tags.get("industrial"),
                        man_made_tag=tags.get("man_made"),
                        power_tag=tags.get("power"),
                        plant_source=tags.get("plant:source") or tags.get("generator:source"),
                        landuse=tags.get("landuse"),
                        tags=tags,
                        geom=func.ST_GeomFromText(wkt_str, 4326),
                        geometry_quality=geom_quality,
                        source_provider="OVERPASS_API",
                        first_ingested_at=now_utc,
                        last_refreshed_at=now_utc,
                    )
                    self.db.add(new_feat)

                ingested_count += 1

            coverage_rec.status = "COMPLETE"
            coverage_rec.completed_at = datetime.now(UTC)
            coverage_rec.feature_count = ingested_count
            await self.db.commit()

            # Invalidate cached UNAVAILABLE profiles in this region
            await self._invalidate_unavailable_profiles_in_bbox(south, west, north, east)

            return coverage_rec

        except Exception as ex:
            logger.error(f"OSM BBox sync failed for query_hash {query_hash}: {ex}")
            await self.db.rollback()
            try:
                coverage_rec.status = "FAILED"
                self.db.add(coverage_rec)
                await self.db.commit()
            except Exception:
                pass
            raise

    async def _invalidate_unavailable_profiles_in_bbox(
        self, south: float, west: float, north: float, east: float
    ) -> None:
        """
        Invalidate cached profiles with context_class = 'UNAVAILABLE' whose observations
        fall within the newly synced bounding box.
        """
        stmt = delete(IndustrialContextProfileModel).where(
            IndustrialContextProfileModel.context_class == "UNAVAILABLE",
            IndustrialContextProfileModel.observation_id.in_(
                select(ThermalObservationModel.observation_id).where(
                    func.ST_Within(
                        ThermalObservationModel.geom,
                        func.ST_MakeEnvelope(west, south, east, north, 4326),
                    )
                )
            ),
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_or_compute_profile(
        self, observation_id: str, radius_m: float = DEFAULT_INDUSTRIAL_RADIUS_M
    ) -> IndustrialContextProfileDTO:
        """
        Get or compute industrial context profile for a single observation_id.
        Uses cached profile if present and valid.
        """
        # 1. Check existing cached profile
        stmt = select(IndustrialContextProfileModel).where(
            IndustrialContextProfileModel.observation_id == observation_id
        )
        res = await self.db.execute(stmt)
        cached = res.scalar_one_or_none()

        if cached and cached.context_class != "UNAVAILABLE":
            return self._model_to_dto(cached)

        # 2. Fetch thermal observation
        obs_stmt = select(ThermalObservationModel).where(
            ThermalObservationModel.observation_id == observation_id
        )
        obs_res = await self.db.execute(obs_stmt)
        obs = obs_res.scalar_one_or_none()

        if not obs:
            now_utc = datetime.now(UTC)
            return IndustrialContextProfileDTO(
                observation_id=observation_id,
                radius_m=radius_m,
                context_class="UNAVAILABLE",
                coverage_status="MISSING",
                evidence_summary={"reason": "Observation not found in database"},
                calculated_at=now_utc,
            )

        # 3. Compute profile
        profile_dto = await self.compute_profile_for_observation(obs, radius_m)

        # 4. Upsert cache in database
        now_utc = datetime.now(UTC)
        if cached:
            cached.radius_m = profile_dto.radius_m
            cached.context_class = profile_dto.context_class
            cached.coverage_status = profile_dto.coverage_status
            cached.nearest_industrial_distance_m = profile_dto.nearest_industrial_distance_m
            if profile_dto.nearest_feature:
                cached.nearest_feature_osm_uid = profile_dto.nearest_feature.osm_uid
                cached.nearest_feature_name = profile_dto.nearest_feature.name
                cached.nearest_feature_category = profile_dto.nearest_feature.feature_category
                cached.nearest_feature_geometry_quality = profile_dto.nearest_feature.geometry_quality
            else:
                cached.nearest_feature_osm_uid = None
                cached.nearest_feature_name = None
                cached.nearest_feature_category = None
                cached.nearest_feature_geometry_quality = None

            cached.nearest_flare_distance_m = profile_dto.nearest_flare_distance_m
            cached.nearest_chimney_distance_m = profile_dto.nearest_chimney_distance_m
            cached.nearest_refinery_distance_m = profile_dto.nearest_refinery_distance_m
            cached.nearest_power_plant_distance_m = profile_dto.nearest_power_plant_distance_m
            cached.nearest_industrial_area_distance_m = profile_dto.nearest_industrial_area_distance_m
            cached.inside_industrial_area = profile_dto.inside_industrial_area

            cached.feature_count_500m = profile_dto.industrial_feature_count_500m
            cached.feature_count_1km = profile_dto.industrial_feature_count_1km
            cached.feature_count_2km = profile_dto.industrial_feature_count_2km
            cached.feature_count_5km = profile_dto.industrial_feature_count_5km

            cached.has_flare_nearby = profile_dto.has_flare_nearby
            cached.has_chimney_nearby = profile_dto.has_chimney_nearby
            cached.has_refinery_nearby = profile_dto.has_refinery_nearby
            cached.has_power_plant_nearby = profile_dto.has_power_plant_nearby
            cached.evidence_summary = profile_dto.evidence_summary
            cached.calculated_at = now_utc
        else:
            new_model = IndustrialContextProfileModel(
                observation_id=observation_id,
                radius_m=profile_dto.radius_m,
                context_class=profile_dto.context_class,
                coverage_status=profile_dto.coverage_status,
                nearest_industrial_distance_m=profile_dto.nearest_industrial_distance_m,
                nearest_feature_osm_uid=profile_dto.nearest_feature.osm_uid if profile_dto.nearest_feature else None,
                nearest_feature_name=profile_dto.nearest_feature.name if profile_dto.nearest_feature else None,
                nearest_feature_category=profile_dto.nearest_feature.feature_category if profile_dto.nearest_feature else None,
                nearest_feature_geometry_quality=profile_dto.nearest_feature.geometry_quality if profile_dto.nearest_feature else None,
                nearest_flare_distance_m=profile_dto.nearest_flare_distance_m,
                nearest_chimney_distance_m=profile_dto.nearest_chimney_distance_m,
                nearest_refinery_distance_m=profile_dto.nearest_refinery_distance_m,
                nearest_power_plant_distance_m=profile_dto.nearest_power_plant_distance_m,
                nearest_industrial_area_distance_m=profile_dto.nearest_industrial_area_distance_m,
                inside_industrial_area=profile_dto.inside_industrial_area,
                feature_count_500m=profile_dto.industrial_feature_count_500m,
                feature_count_1km=profile_dto.industrial_feature_count_1km,
                feature_count_2km=profile_dto.industrial_feature_count_2km,
                feature_count_5km=profile_dto.industrial_feature_count_5km,
                has_flare_nearby=profile_dto.has_flare_nearby,
                has_chimney_nearby=profile_dto.has_chimney_nearby,
                has_refinery_nearby=profile_dto.has_refinery_nearby,
                has_power_plant_nearby=profile_dto.has_power_plant_nearby,
                evidence_summary=profile_dto.evidence_summary,
                algorithm_version="1.0.0",
                osm_snapshot_at=profile_dto.osm_snapshot_at,
                calculated_at=now_utc,
            )
            self.db.add(new_model)

        await self.db.commit()
        return profile_dto

    async def compute_profile_for_observation(
        self, obs: ThermalObservationModel, radius_m: float = DEFAULT_INDUSTRIAL_RADIUS_M
    ) -> IndustrialContextProfileDTO:
        """
        Execute metric PostGIS spatial query and full envelope coverage verification for observation.
        """
        now_utc = datetime.now(UTC)
        coverage_status, osm_snapshot = await self.check_envelope_coverage(obs.latitude, obs.longitude, radius_m)

        if coverage_status not in ("ADEQUATE", "PARTIAL"):
            return IndustrialContextProfileDTO(
                observation_id=obs.observation_id,
                radius_m=radius_m,
                context_class="UNAVAILABLE",
                coverage_status=coverage_status,
                evidence_summary={"reason": "Incomplete or missing 5km spatial OSM coverage"},
                osm_snapshot_at=osm_snapshot,
                calculated_at=now_utc,
            )

        # Execute PostGIS ST_Distance(geography), ST_DWithin, and ST_Covers query
        spatial_sql = text("""
            SELECT
                f.osm_uid,
                f.name,
                f.operator,
                f.feature_category,
                f.geometry_quality,
                ST_Distance(obs.geom::geography, f.geom::geography) as distance_m,
                (CASE
                    WHEN f.geometry_quality = 'EXACT_POLYGON' AND ST_Covers(f.geom, obs.geom) THEN true
                    ELSE false
                END) as is_contained
            FROM thermal_observations obs
            CROSS JOIN osm_industrial_features f
            WHERE obs.observation_id = :obs_id
              AND ST_DWithin(obs.geom::geography, f.geom::geography, :radius_m)
            ORDER BY distance_m ASC
        """)
        res = await self.db.execute(spatial_sql, {"obs_id": obs.observation_id, "radius_m": radius_m})
        rows = res.fetchall()

        if not rows:
            return IndustrialContextProfileDTO(
                observation_id=obs.observation_id,
                radius_m=radius_m,
                context_class="NONE",
                coverage_status=coverage_status,
                evidence_summary={
                    "reason": "Full 5km OSM coverage present, 0 industrial features found"
                    if coverage_status == "ADEQUATE"
                    else "Partial spatial OSM coverage present, 0 industrial features found"
                },
                osm_snapshot_at=osm_snapshot,
                calculated_at=now_utc,
            )

        # Parse features and distance metrics
        nearest_row = rows[0]
        nearest_dto = NearestFeatureDTO(
            osm_uid=nearest_row.osm_uid,
            name=nearest_row.name,
            operator=nearest_row.operator,
            feature_category=nearest_row.feature_category,
            geometry_quality=nearest_row.geometry_quality,
            distance_m=round(float(nearest_row.distance_m), 2),
            inside_industrial_area=bool(nearest_row.is_contained),
        )

        inside_area = any(bool(r.is_contained) for r in rows)
        count_500m = sum(1 for r in rows if float(r.distance_m) <= 500.0)
        count_1km = sum(1 for r in rows if float(r.distance_m) <= 1000.0)
        count_2km = sum(1 for r in rows if float(r.distance_m) <= 2000.0)
        count_5km = len(rows)

        def get_min_dist(cat_name: str) -> float | None:
            cat_rows = [float(r.distance_m) for r in rows if r.feature_category == cat_name]
            return round(min(cat_rows), 2) if cat_rows else None

        min_flare = get_min_dist("FLARE")
        min_chimney = get_min_dist("CHIMNEY")
        min_refinery = get_min_dist("REFINERY")
        min_power = get_min_dist("THERMAL_POWER_PLANT") or get_min_dist("OTHER_POWER_PLANT")
        min_area = get_min_dist("INDUSTRIAL_AREA")

        nearest_dist = nearest_dto.distance_m

        # Determine context strength
        if inside_area or (min_flare is not None and min_flare <= 1000.0) or (min_refinery is not None and min_refinery <= 1000.0):
            context_class: ContextClass = "STRONG"
        elif nearest_dist <= 2000.0 or (min_chimney is not None and min_chimney <= 2000.0) or (min_power is not None and min_power <= 2000.0):
            context_class = "MODERATE"
        else:
            context_class = "WEAK"

        return IndustrialContextProfileDTO(
            observation_id=obs.observation_id,
            radius_m=radius_m,
            context_class=context_class,
            coverage_status=coverage_status,
            nearest_industrial_distance_m=nearest_dist,
            nearest_feature=nearest_dto,
            nearest_flare_distance_m=min_flare,
            nearest_chimney_distance_m=min_chimney,
            nearest_refinery_distance_m=min_refinery,
            nearest_power_plant_distance_m=min_power,
            nearest_industrial_area_distance_m=min_area,
            inside_industrial_area=inside_area,
            industrial_feature_count_500m=count_500m,
            industrial_feature_count_1km=count_1km,
            industrial_feature_count_2km=count_2km,
            industrial_feature_count_5km=count_5km,
            has_flare_nearby=min_flare is not None and min_flare <= 5000.0,
            has_chimney_nearby=min_chimney is not None and min_chimney <= 5000.0,
            has_refinery_nearby=min_refinery is not None and min_refinery <= 5000.0,
            has_power_plant_nearby=min_power is not None and min_power <= 5000.0,
            evidence_summary={
                "nearest_category": nearest_dto.feature_category,
                "distance_m": nearest_dist,
                "inside_area": inside_area,
                "feature_counts": {"500m": count_500m, "1km": count_1km, "2km": count_2km, "5km": count_5km},
            },
            osm_snapshot_at=osm_snapshot,
            calculated_at=now_utc,
        )

    def _model_to_dto(self, model: IndustrialContextProfileModel) -> IndustrialContextProfileDTO:
        nearest_dto = None
        if model.nearest_feature_osm_uid and model.nearest_feature_category:
            nearest_dto = NearestFeatureDTO(
                osm_uid=model.nearest_feature_osm_uid,
                name=model.nearest_feature_name,
                operator=None,
                feature_category=model.nearest_feature_category,  # type: ignore
                geometry_quality=model.nearest_feature_geometry_quality or "EXACT_POINT",  # type: ignore
                distance_m=model.nearest_industrial_distance_m or 0.0,
                inside_industrial_area=model.inside_industrial_area,
            )

        return IndustrialContextProfileDTO(
            observation_id=model.observation_id,
            radius_m=model.radius_m,
            context_class=model.context_class,  # type: ignore
            coverage_status=model.coverage_status,  # type: ignore
            nearest_industrial_distance_m=model.nearest_industrial_distance_m,
            nearest_feature=nearest_dto,
            nearest_flare_distance_m=model.nearest_flare_distance_m,
            nearest_chimney_distance_m=model.nearest_chimney_distance_m,
            nearest_refinery_distance_m=model.nearest_refinery_distance_m,
            nearest_power_plant_distance_m=model.nearest_power_plant_distance_m,
            nearest_industrial_area_distance_m=model.nearest_industrial_area_distance_m,
            inside_industrial_area=model.inside_industrial_area,
            industrial_feature_count_500m=model.feature_count_500m,
            industrial_feature_count_1km=model.feature_count_1km,
            industrial_feature_count_2km=model.feature_count_2km,
            industrial_feature_count_5km=model.feature_count_5km,
            has_flare_nearby=model.has_flare_nearby,
            has_chimney_nearby=model.has_chimney_nearby,
            has_refinery_nearby=model.has_refinery_nearby,
            has_power_plant_nearby=model.has_power_plant_nearby,
            evidence_summary=model.evidence_summary or {},
            algorithm_version=model.algorithm_version,
            osm_snapshot_at=model.osm_snapshot_at,
            calculated_at=model.calculated_at,
        )
