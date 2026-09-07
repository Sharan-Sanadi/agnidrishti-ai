-- AGNIDRISHTI — Phase 0 Initial Schema Migration
-- Enables PostGIS and prepares tables for thermal data and classification.

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 1. THERMAL DETECTIONS (Raw / Base Hotspots)
-- ==========================================
CREATE TABLE public.thermal_detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL,                  -- e.g., 'NASA_FIRMS'
    satellite TEXT,                        -- e.g., 'MODIS', 'VIIRS'
    acquired_at TIMESTAMPTZ NOT NULL,      -- UTC timestamp of detection
    
    -- We store explicit lat/lng for easy debugging and standard JSON APIs
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    
    -- PostGIS geography point for spatial queries (Distance, Within)
    geom geometry(Point, 4326) NOT NULL,
    
    frp_mw DOUBLE PRECISION,
    brightness_ti4 DOUBLE PRECISION,
    brightness_ti5 DOUBLE PRECISION,
    confidence TEXT,                       -- Source confidence (e.g. low/nominal/high)
    day_night VARCHAR(1),                  -- 'D' or 'N'
    
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent exact duplicates from the same source
    UNIQUE(source, satellite, acquired_at, latitude, longitude)
);

-- Spatial index
CREATE INDEX idx_thermal_detections_geom ON public.thermal_detections USING GIST (geom);
-- Time index
CREATE INDEX idx_thermal_detections_acquired_at ON public.thermal_detections (acquired_at);

-- ==========================================
-- 2. INDUSTRIAL FEATURES
-- ==========================================
CREATE TABLE public.industrial_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL,                  -- e.g., 'OSM'
    feature_type TEXT NOT NULL,            -- e.g., 'factory', 'power_plant', 'mine'
    name TEXT,
    
    geom geometry(Geometry, 4326) NOT NULL, -- Point or Polygon
    
    metadata JSONB DEFAULT '{}'::jsonb,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_industrial_features_geom ON public.industrial_features USING GIST (geom);

-- ==========================================
-- 3. HOTSPOT CLASSIFICATIONS
-- ==========================================
CREATE TABLE public.hotspot_classifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thermal_detection_id UUID REFERENCES public.thermal_detections(id) ON DELETE CASCADE,
    
    top_level_class TEXT NOT NULL,         -- INDUSTRIAL / NON_INDUSTRIAL / UNCERTAIN
    subclass TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    
    evidence JSONB DEFAULT '[]'::jsonb,
    reasoning_summary TEXT,
    model_version TEXT NOT NULL,
    data_quality TEXT,
    requires_ground_verification BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- 4. ALERTS / MONITORING
-- ==========================================
CREATE TABLE public.alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thermal_detection_id UUID REFERENCES public.thermal_detections(id) ON DELETE SET NULL,
    alert_type TEXT NOT NULL,              -- e.g., 'NEW_INDUSTRIAL_ANOMALY', 'PERSISTENT_SOURCE'
    severity TEXT NOT NULL,                -- e.g., 'INFO', 'WARNING', 'CRITICAL'
    message TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN',            -- 'OPEN', 'ACKNOWLEDGED', 'RESOLVED'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Note: RLS policies will be added in Phase 2.
-- For Phase 0, we do not require a database connection to boot the app.
