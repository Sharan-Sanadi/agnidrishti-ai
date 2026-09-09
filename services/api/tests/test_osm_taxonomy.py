# AGNIDRISHTI API — OSM Industrial Taxonomy Tests
from app.providers.overpass import classify_osm_taxonomy


def test_taxonomy_precedence_flare():
    tags = {"man_made": "flare", "industrial": "refinery", "power": "plant"}
    cat, rel = classify_osm_taxonomy(tags)
    assert cat == "FLARE"
    assert rel == "HIGH"


def test_taxonomy_precedence_refinery():
    tags = {"industrial": "refinery", "man_made": "works"}
    cat, rel = classify_osm_taxonomy(tags)
    assert cat == "REFINERY"
    assert rel == "HIGH"


def test_taxonomy_precedence_chimney():
    tags = {"man_made": "chimney", "landuse": "industrial"}
    cat, rel = classify_osm_taxonomy(tags)
    assert cat == "CHIMNEY"
    assert rel == "HIGH"


def test_thermal_power_plant_coal():
    tags = {"power": "plant", "plant:source": "coal"}
    cat, rel = classify_osm_taxonomy(tags)
    assert cat == "THERMAL_POWER_PLANT"
    assert rel == "HIGH"


def test_thermal_power_plant_gas():
    tags = {"power": "plant", "generator:source": "gas"}
    cat, rel = classify_osm_taxonomy(tags)
    assert cat == "THERMAL_POWER_PLANT"
    assert rel == "HIGH"


def test_nonthermal_power_plant_solar():
    tags = {"power": "plant", "plant:source": "solar"}
    cat, rel = classify_osm_taxonomy(tags)
    assert cat == "OTHER_POWER_PLANT"
    assert rel == "LOW"


def test_industrial_works():
    tags = {"man_made": "works"}
    cat, rel = classify_osm_taxonomy(tags)
    assert cat == "INDUSTRIAL_WORKS"
    assert rel == "MEDIUM"


def test_industrial_area():
    tags = {"landuse": "industrial"}
    cat, rel = classify_osm_taxonomy(tags)
    assert cat == "INDUSTRIAL_AREA"
    assert rel == "MEDIUM"


def test_storage_tank():
    tags = {"man_made": "storage_tank"}
    cat, rel = classify_osm_taxonomy(tags)
    assert cat == "STORAGE_TANK"
    assert rel == "MEDIUM"
