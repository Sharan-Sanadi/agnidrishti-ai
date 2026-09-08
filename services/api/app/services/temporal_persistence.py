# AGNIDRISHTI API — Temporal Persistence Intelligence Service
"""
Production service for computing PostGIS-backed temporal persistence intelligence.
Analyzes satellite thermal activity over time using spatial proximity and UTC date recurrence.
Enforces strict no-future-data leakage, coverage gating, and transparent V1 heuristic classification.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.thermal_observation import ThermalObservationModel
from app.db.repositories.firms_coverage import FIRMSCoverageRepository
from app.db.repositories.thermal_observation import ThermalObservationRepository

settings = get_settings()


class TemporalPersistenceProfile:
    """Canonical data structure for computed Phase 3 Persistence Profile."""

    def __init__(
        self,
        observation_id: str,
        target_time: datetime,
        radius_m: float,
        algorithm_version: str,
        raw_detection_count_7d: int,
        raw_detection_count_30d: int,
        active_days_7d: int,
        active_days_30d: int,
        active_weeks_30d: int,
        first_seen_30d: datetime | None,
        last_seen_30d: datetime | None,
        temporal_span_days_30d: float,
        history_coverage_days_7d: int,
        history_coverage_days_30d: int,
        history_coverage_ratio_30d: float,
        persistence_index: int,
        persistence_class: str,
        explanation: str,
        score_components: dict[str, float],
    ) -> None:
        self.observation_id = observation_id
        self.target_time = target_time
        self.radius_m = radius_m
        self.algorithm_version = algorithm_version

        self.raw_detection_count_7d = raw_detection_count_7d
        self.raw_detection_count_30d = raw_detection_count_30d

        self.active_days_7d = active_days_7d
        self.active_days_30d = active_days_30d
        self.active_weeks_30d = active_weeks_30d

        self.first_seen_30d = first_seen_30d
        self.last_seen_30d = last_seen_30d
        self.temporal_span_days_30d = temporal_span_days_30d

        self.history_coverage_days_7d = history_coverage_days_7d
        self.history_coverage_days_30d = history_coverage_days_30d
        self.history_coverage_ratio_30d = history_coverage_ratio_30d

        self.persistence_index = persistence_index
        self.persistence_class = persistence_class
        self.explanation = explanation
        self.score_components = score_components

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "analysis_as_of": self.target_time.isoformat(),
            "radius_m": self.radius_m,
            "algorithm_version": self.algorithm_version,
            "raw_detection_count_7d": self.raw_detection_count_7d,
            "raw_detection_count_30d": self.raw_detection_count_30d,
            "active_days_7d": self.active_days_7d,
            "active_days_30d": self.active_days_30d,
            "active_weeks_30d": self.active_weeks_30d,
            "first_seen_30d": self.first_seen_30d.isoformat() if self.first_seen_30d else None,
            "last_seen_30d": self.last_seen_30d.isoformat() if self.last_seen_30d else None,
            "temporal_span_days_30d": round(self.temporal_span_days_30d, 1),
            "history_coverage_days_7d": self.history_coverage_days_7d,
            "history_coverage_days_30d": self.history_coverage_days_30d,
            "history_coverage_ratio_30d": round(self.history_coverage_ratio_30d, 2),
            "persistence_index": self.persistence_index,
            "persistence_class": self.persistence_class,
            "explanation": self.explanation,
            "score_components": self.score_components,
        }


def compute_persistence_index_v1(
    active_days_30d: int,
    span_days: float,
    active_weeks_30d: int,
    active_days_7d: int,
) -> tuple[int, dict[str, float]]:
    """
    Compute deterministic Phase 3 Persistence Index V1 (0-100).
    A. Distinct active days (max 45)
    B. Temporal span (max 25)
    C. Multi-week recurrence (max 20)
    D. Recent recurrence (max 10)
    """
    comp_a = min(active_days_30d / 8.0, 1.0) * 45.0
    comp_b = min(span_days / 21.0, 1.0) * 25.0
    comp_c = min(active_weeks_30d / 4.0, 1.0) * 20.0
    comp_d = min(active_days_7d / 2.0, 1.0) * 10.0

    raw_total = comp_a + comp_b + comp_c + comp_d
    final_score = max(0, min(100, round(raw_total)))

    components = {
        "active_days_score": round(comp_a, 1),
        "temporal_span_score": round(comp_b, 1),
        "multi_week_score": round(comp_c, 1),
        "recency_score": round(comp_d, 1),
    }

    return final_score, components


def classify_persistence_v1(
    active_days_30d: int,
    active_weeks_30d: int,
    span_days: float,
    coverage_days_30d: int,
    min_history_days: int = 21,
) -> str:
    """
    Classify thermal observation persistence using deterministic V1 rules.
    1. Gate on dataset history coverage: if coverage_days < min_history_days -> INSUFFICIENT_HISTORY
    2. Classify based on recurrence:
       - PERSISTENT: active_days >= 8 AND active_weeks >= 3 AND span >= 14
       - RECURRING: active_days >= 4 AND span >= 7
       - OCCASIONAL: active_days in [2, 3]
       - ISOLATED: active_days <= 1
    """
    if coverage_days_30d < min_history_days:
        return "INSUFFICIENT_HISTORY"

    if active_days_30d >= 8 and active_weeks_30d >= 3 and span_days >= 14.0:
        return "PERSISTENT"

    if active_days_30d >= 4 and span_days >= 7.0:
        return "RECURRING"

    if active_days_30d >= 2:
        return "OCCASIONAL"

    return "ISOLATED"


def generate_explanation_v1(
    persistence_class: str,
    active_days_30d: int,
    active_weeks_30d: int,
    radius_m: float,
    coverage_days_30d: int,
) -> str:
    """Generate deterministic, scientifically honest explanation without hallucinated causes."""
    if persistence_class == "INSUFFICIENT_HISTORY":
        return f"Only {coverage_days_30d} of requested 30 historical days have been queried. Additional FIRMS history is required to determine persistence reliably."

    if persistence_class == "PERSISTENT":
        return f"Persistent thermal activity observed on {active_days_30d} distinct days across {active_weeks_30d} weeks within {int(radius_m)}m over the previous 30 days."

    if persistence_class == "RECURRING":
        return f"Recurring thermal activity detected on {active_days_30d} distinct days across {active_weeks_30d} weeks within {int(radius_m)}m over the previous 30 days."

    if persistence_class == "OCCASIONAL":
        return f"Occasional thermal activity observed on {active_days_30d} distinct days within {int(radius_m)}m over the previous 30 days."

    return f"Isolated thermal activity with only {active_days_30d} active day observed in a verified 30-day history within {int(radius_m)}m."


class TemporalPersistenceService:
    """
    Core service calculating Phase 3 Temporal Persistence Intelligence.
    Uses PostGIS ST_DWithin spatial queries and strict UTC temporal grouping.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.obs_repo = ThermalObservationRepository(db)
        self.coverage_repo = FIRMSCoverageRepository(db)

    async def analyze_observation(
        self,
        observation: ThermalObservationModel,
        radius_m: float | None = None,
        lookback_days: int = 30,
        min_history_days: int | None = None,
    ) -> TemporalPersistenceProfile:
        """
        Analyze a target observation for temporal persistence.
        Guarantees NO FUTURE DATA LEAKAGE: candidate observations > target.acquisition_time_utc are excluded.
        """
        eff_radius = radius_m if radius_m is not None else settings.persistence_radius_meters
        eff_min_history = (
            min_history_days if min_history_days is not None else settings.persistence_min_history_days
        )
        # Bound radius safely (250m to 2000m)
        eff_radius = max(250.0, min(eff_radius, 2000.0))

        target_time = observation.acquisition_time_utc

        # 1. Fetch spatiotemporal candidates <= target_time within radius
        candidates = await self.obs_repo.get_spatiotemporal_neighbors(
            target_latitude=observation.latitude,
            target_longitude=observation.longitude,
            target_time=target_time,
            radius_m=eff_radius,
            lookback_days=lookback_days,
        )

        # 2. Filter 7-day vs 30-day windows
        time_7d_cutoff = target_time - timedelta(days=7)
        cands_7d = [c for c in candidates if c.acquisition_time_utc >= time_7d_cutoff]
        cands_30d = candidates

        raw_count_7d = len(cands_7d)
        raw_count_30d = len(cands_30d)

        # 3. Compute distinct active UTC dates
        active_dates_7d = {c.acquisition_time_utc.date() for c in cands_7d}
        active_dates_30d = {c.acquisition_time_utc.date() for c in cands_30d}

        active_days_7d = len(active_dates_7d)
        active_days_30d = len(active_dates_30d)

        # 4. Compute active calendar weeks (year, iso_week)
        active_weeks_set = {c.acquisition_time_utc.isocalendar()[:2] for c in cands_30d}
        active_weeks_30d = len(active_weeks_set)

        # 5. First & last seen timestamps
        if cands_30d:
            acq_times = [c.acquisition_time_utc for c in cands_30d]
            first_seen_30d = min(acq_times)
            last_seen_30d = max(acq_times)
            span_days = max(0.0, (last_seen_30d - first_seen_30d).total_seconds() / 86400.0)
        else:
            first_seen_30d = target_time
            last_seen_30d = target_time
            span_days = 0.0

        # 6. Verify history query coverage
        start_date_30d = (target_time - timedelta(days=30)).date()
        start_date_7d = (target_time - timedelta(days=7)).date()
        target_date = target_time.date()

        covered_days_30d = await self.coverage_repo.get_covered_days(
            start_date=start_date_30d,
            end_date=target_date,
        )
        covered_days_7d = await self.coverage_repo.get_covered_days(
            start_date=start_date_7d,
            end_date=target_date,
        )

        # If no coverage records yet (e.g. fresh installation before backfill or single sync), fallback to checking total DB days span
        if covered_days_30d == 0:
            total_db_records = await self.obs_repo.count_total()
            if total_db_records > 0:
                # If we have stored observations, assume current queried window has available DB coverage
                covered_days_30d = min(30, max(1, active_days_30d))
                covered_days_7d = min(7, max(1, active_days_7d))

        coverage_ratio_30d = min(1.0, covered_days_30d / 30.0)

        # 7. Persistence Index V1 & Classification
        p_index, score_comps = compute_persistence_index_v1(
            active_days_30d=active_days_30d,
            span_days=span_days,
            active_weeks_30d=active_weeks_30d,
            active_days_7d=active_days_7d,
        )

        p_class = classify_persistence_v1(
            active_days_30d=active_days_30d,
            active_weeks_30d=active_weeks_30d,
            span_days=span_days,
            coverage_days_30d=covered_days_30d,
            min_history_days=eff_min_history,
        )

        explanation = generate_explanation_v1(
            persistence_class=p_class,
            active_days_30d=active_days_30d,
            active_weeks_30d=active_weeks_30d,
            radius_m=eff_radius,
            coverage_days_30d=covered_days_30d,
        )

        return TemporalPersistenceProfile(
            observation_id=observation.observation_id,
            target_time=target_time,
            radius_m=eff_radius,
            algorithm_version=settings.persistence_algorithm_version,
            raw_detection_count_7d=raw_count_7d,
            raw_detection_count_30d=raw_count_30d,
            active_days_7d=active_days_7d,
            active_days_30d=active_days_30d,
            active_weeks_30d=active_weeks_30d,
            first_seen_30d=first_seen_30d,
            last_seen_30d=last_seen_30d,
            temporal_span_days_30d=span_days,
            history_coverage_days_7d=covered_days_7d,
            history_coverage_days_30d=covered_days_30d,
            history_coverage_ratio_30d=coverage_ratio_30d,
            persistence_index=p_index,
            persistence_class=p_class,
            explanation=explanation,
            score_components=score_comps,
        )

    async def analyze_batch(
        self,
        observations: list[ThermalObservationModel],
        radius_m: float | None = None,
        lookback_days: int = 30,
    ) -> list[TemporalPersistenceProfile]:
        """Analyze a list of observations efficiently."""
        profiles = []
        for obs in observations:
            prof = await self.analyze_observation(
                observation=obs,
                radius_m=radius_m,
                lookback_days=lookback_days,
            )
            profiles.append(prof)
        return profiles
