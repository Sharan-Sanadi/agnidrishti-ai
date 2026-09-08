# AGNIDRISHTI API — NASA FIRMS CSV Parser
"""
Defensive CSV parser for NASA FIRMS satellite thermal observations.

Handles:
- Header-based column mapping (tolerant to column order & future columns)
- Acq_time normalization (leading zero preservation, e.g. '758' -> '07:58', '35' -> '00:35')
- Timezone-aware UTC timestamp creation
- Deterministic observation ID generation via SHA-256
- Robust numeric parsing and malformed record tracking
- GeoJSON Point geometry in [longitude, latitude] order
"""

from __future__ import annotations

import csv
import hashlib
import io
from datetime import UTC, datetime

from app.core.logging import logger
from app.schemas.firms import ThermalObservation


def normalize_acq_time(raw_time: str) -> tuple[int, int, str]:
    """
    Normalize raw FIRMS acq_time (e.g. '758', '0035', '1420') into (hours, minutes, 'HH:MM').
    Preserves leading zeros accurately.
    """
    clean = raw_time.strip()
    # Pad to 4 digits: e.g. '758' -> '0758', '35' -> '0035', '5' -> '0005'
    padded = clean.zfill(4)
    if len(padded) > 4:
        # Unexpected length: truncate to last 4
        padded = padded[-4:]

    hour = int(padded[:2])
    minute = int(padded[2:])

    # Guard bounds
    hour = max(0, min(23, hour))
    minute = max(0, min(59, minute))

    return hour, minute, f"{hour:02d}:{minute:02d}"


def generate_observation_id(
    source: str,
    satellite: str,
    acq_iso: str,
    latitude: float,
    longitude: float,
) -> str:
    """
    Generate a stable, deterministic observation identifier.
    The same physical satellite observation will receive the identical ID across fetches.
    """
    key = f"{source.strip().upper()}:{satellite.strip().upper()}:{acq_iso}:{latitude:.5f}:{longitude:.5f}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return f"firms_{digest[:20]}"


def parse_firms_csv(
    csv_content: str,
    source_name: str,
) -> tuple[list[ThermalObservation], int]:
    """
    Parse NASA FIRMS CSV response into canonical ThermalObservation objects.

    Returns:
        tuple of (valid_observations, rejected_count)
    """
    if not csv_content or not csv_content.strip():
        return [], 0

    reader = csv.DictReader(io.StringIO(csv_content.strip()))
    if not reader.fieldnames:
        return [], 0

    # Normalize header mapping (strip whitespace, lowercase)
    field_map: dict[str, str] = {f.strip().lower(): f for f in reader.fieldnames}

    # Verify minimum required fields exist
    required = ["latitude", "longitude", "acq_date", "acq_time"]
    missing = [req for req in required if req not in field_map]
    if missing:
        logger.error(f"NASA FIRMS CSV missing critical columns: {missing}. Available: {reader.fieldnames}")
        return [], 0

    observations: list[ThermalObservation] = []
    rejected_count = 0
    now_utc = datetime.now(UTC)

    for row_idx, raw_row in enumerate(reader):
        try:
            # Clean keys
            row = {k.strip().lower(): (v.strip() if v is not None else "") for k, v in raw_row.items() if k}

            raw_lat = row.get("latitude", "")
            raw_lng = row.get("longitude", "")
            raw_date = row.get("acq_date", "")
            raw_time = row.get("acq_time", "")

            if not raw_lat or not raw_lng or not raw_date or not raw_time:
                rejected_count += 1
                continue

            lat = float(raw_lat)
            lng = float(raw_lng)

            # Spatial validation
            if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
                rejected_count += 1
                continue

            # Parse acquisition timestamp
            hour, minute, _ = normalize_acq_time(raw_time)
            # acq_date is expected in YYYY-MM-DD format
            date_parts = [int(p) for p in raw_date.split("-")]
            if len(date_parts) != 3:
                rejected_count += 1
                continue
            year, month, day = date_parts
            acq_dt = datetime(year, month, day, hour, minute, tzinfo=UTC)
            acq_iso = acq_dt.isoformat()

            # Metadata fields
            satellite = row.get("satellite") or "UNKNOWN"
            instrument = row.get("instrument") or "VIIRS"
            confidence = row.get("confidence") or "nominal"
            daynight = (row.get("daynight") or "").upper() or None
            firms_version = row.get("version") or None

            # Safe numeric conversions
            def safe_float(val: str) -> float | None:
                if not val or val.lower() in ("nan", "null", "none"):
                    return None
                try:
                    return float(val)
                except ValueError:
                    return None

            frp = safe_float(row.get("frp", ""))
            bright_ti4 = safe_float(row.get("bright_ti4", ""))
            bright_ti5 = safe_float(row.get("bright_ti5", ""))
            scan = safe_float(row.get("scan", ""))
            track = safe_float(row.get("track", ""))

            obs_id = generate_observation_id(
                source=source_name,
                satellite=satellite,
                acq_iso=acq_iso,
                latitude=lat,
                longitude=lng,
            )

            # Build GeoJSON Point geometry in [longitude, latitude] order
            geojson_geom = {
                "type": "Point",
                "coordinates": [lng, lat],
            }

            obs = ThermalObservation(
                id=obs_id,
                latitude=lat,
                longitude=lng,
                acquisition_time_utc=acq_dt,
                satellite=satellite,
                instrument=instrument,
                source=source_name,
                confidence=confidence,
                frp=frp,
                bright_ti4=bright_ti4,
                bright_ti5=bright_ti5,
                scan=scan,
                track=track,
                daynight=daynight,
                firms_version=firms_version,
                ingestion_time_utc=now_utc,
                geojson=geojson_geom,
            )
            observations.append(obs)

        except Exception as ex:
            rejected_count += 1
            logger.debug(f"Skipping malformed FIRMS row {row_idx}: {ex}")

    return observations, rejected_count
