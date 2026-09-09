# AGNIDRISHTI API — OSM Geometry Normalization Tests
from app.providers.overpass import normalize_osm_geometry


def test_normalize_node_point():
    elem = {"type": "node", "id": 123, "lat": 20.5, "lon": 78.5}
    wkt, quality, geom = normalize_osm_geometry(elem)
    assert quality == "EXACT_POINT"
    assert "POINT (78.5 20.5)" in wkt


def test_normalize_closed_way_polygon():
    elem = {
        "type": "way",
        "id": 456,
        "geometry": [
            {"lat": 20.0, "lon": 78.0},
            {"lat": 20.1, "lon": 78.0},
            {"lat": 20.1, "lon": 78.1},
            {"lat": 20.0, "lon": 78.0},
        ],
    }
    wkt, quality, geom = normalize_osm_geometry(elem)
    assert quality == "EXACT_POLYGON"
    assert "POLYGON" in wkt


def test_normalize_open_way_linestring():
    elem = {
        "type": "way",
        "id": 789,
        "geometry": [
            {"lat": 20.0, "lon": 78.0},
            {"lat": 20.1, "lon": 78.1},
        ],
    }
    wkt, quality, geom = normalize_osm_geometry(elem)
    assert quality == "EXACT_LINE"
    assert "LINESTRING" in wkt


def test_normalize_relation_center_fallback():
    elem = {"type": "relation", "id": 999, "center": {"lat": 21.0, "lon": 79.0}}
    wkt, quality, geom = normalize_osm_geometry(elem)
    assert quality == "CENTER_FALLBACK"
    assert "POINT (79 21)" in wkt
