# AGNIDRISHTI API — OpenStreetMap Industrial Feature Normalizer
from __future__ import annotations

from typing import Any

from shapely.geometry import LineString, Point, Polygon

THERMAL_PLANT_SOURCES = {
    "coal",
    "gas",
    "oil",
    "biomass",
    "waste",
    "geothermal",
    "lignite",
    "diesel",
    "petcoke",
    "synfuel",
}


def classify_osm_taxonomy(tags: dict[str, Any]) -> tuple[str, str]:
    """
    Classify raw OSM tags into deterministic industrial taxonomy with precedence.
    Returns (feature_category, thermal_relevance).

    Precedence Order:
    1. man_made=flare -> FLARE (HIGH)
    2. industrial=refinery -> REFINERY (HIGH)
    3. man_made=chimney -> CHIMNEY (HIGH)
    4. power=plant + thermal source -> THERMAL_POWER_PLANT (HIGH)
    5. man_made=works -> INDUSTRIAL_WORKS (MEDIUM)
    6. landuse=industrial -> INDUSTRIAL_AREA (MEDIUM)
    7. man_made=storage_tank -> STORAGE_TANK (MEDIUM)
    8. power=plant (non-thermal or unknown) -> OTHER_POWER_PLANT (LOW)
    9. Other industrial tags -> OTHER_INDUSTRIAL (LOW)
    """
    man_made = tags.get("man_made", "").lower()
    industrial = tags.get("industrial", "").lower()
    power = tags.get("power", "").lower()
    plant_source = tags.get("plant:source", "").lower() or tags.get("generator:source", "").lower()
    landuse = tags.get("landuse", "").lower()

    if man_made == "flare":
        return "FLARE", "HIGH"

    if industrial == "refinery":
        return "REFINERY", "HIGH"

    if man_made == "chimney":
        return "CHIMNEY", "HIGH"

    if power == "plant":
        sources = {s.strip() for s in plant_source.split(";") if s.strip()}
        if sources.intersection(THERMAL_PLANT_SOURCES):
            return "THERMAL_POWER_PLANT", "HIGH"
        return "OTHER_POWER_PLANT", "LOW"

    if man_made == "works":
        return "INDUSTRIAL_WORKS", "MEDIUM"

    if landuse == "industrial":
        return "INDUSTRIAL_AREA", "MEDIUM"

    if man_made == "storage_tank":
        return "STORAGE_TANK", "MEDIUM"

    if industrial or man_made:
        return "OTHER_INDUSTRIAL", "LOW"

    return "OTHER_INDUSTRIAL", "LOW"


def normalize_osm_geometry(element: dict[str, Any]) -> tuple[str, str, Any]:
    """
    Convert raw Overpass JSON element into (WKT/geometry_dict, geometry_quality, WKT_string).

    Supports:
    - Node -> Point (EXACT_POINT)
    - Open Way -> LineString (EXACT_LINE)
    - Closed Way -> Polygon (EXACT_POLYGON)
    - Relation / Center Fallback -> Point (CENTER_FALLBACK)
    """
    elem_type = element.get("type", "node")

    # 1. Point / Node
    if elem_type == "node" or ("lat" in element and "lon" in element and "geometry" not in element and "nodes" not in element):
        lat = element.get("lat")
        lon = element.get("lon")
        if lat is not None and lon is not None:
            pt = Point(float(lon), float(lat))
            return pt.wkt, "EXACT_POINT", pt

    # 2. Way
    if elem_type == "way":
        geom_coords = element.get("geometry", [])
        if geom_coords:
            coords = [(pt["lon"], pt["lat"]) for pt in geom_coords]
            if len(coords) >= 3 and coords[0] == coords[-1]:
                try:
                    poly = Polygon(coords)
                    if poly.is_valid and poly.area > 0:
                        return poly.wkt, "EXACT_POLYGON", poly
                except Exception:
                    pass
            if len(coords) >= 2:
                try:
                    line = LineString(coords)
                    if line.is_valid:
                        return line.wkt, "EXACT_LINE", line
                except Exception:
                    pass

    # 3. Center Fallback for Relations / Complex elements
    center = element.get("center", {})
    if "lat" in center and "lon" in center:
        pt = Point(float(center["lon"]), float(center["lat"]))
        return pt.wkt, "CENTER_FALLBACK", pt

    if "lat" in element and "lon" in element:
        pt = Point(float(element["lon"]), float(element["lat"]))
        return pt.wkt, "CENTER_FALLBACK", pt

    # Fallback default point (0, 0)
    pt = Point(0.0, 0.0)
    return pt.wkt, "CENTER_FALLBACK", pt
