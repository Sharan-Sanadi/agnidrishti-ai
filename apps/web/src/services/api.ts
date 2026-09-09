import axios from 'axios';

const rawBaseUrl = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const API_BASE_URL = rawBaseUrl.endsWith('/api/v1') ? rawBaseUrl : `${rawBaseUrl.replace(/\/$/, '')}/api/v1`;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ThermalObservation {
  id: string;
  latitude: number;
  longitude: number;
  acquisition_time_utc: string;
  satellite: string;
  instrument: string;
  source: string;
  confidence: string;
  confidence_normalized?: string | null;
  frp?: number | null;
  bright_ti4?: number | null;
  bright_ti5?: number | null;
  scan?: number | null;
  track?: number | null;
  daynight?: string | null;
  firms_version?: string | null;
  ingestion_time_utc?: string;
  first_ingested_at?: string;
  last_seen_at?: string;
  ingestion_count?: number;
  stored_in_postgis?: boolean;
  frp_mw?: number | null;
  acquired_at?: string;
  is_live_firms?: boolean;
  geojson?: {
    type: string;
    coordinates: [number, number]; // [longitude, latitude]
  };
}

export interface FIRMSSyncResponse {
  status: string;
  run_id: string;
  provider: string;
  sources: string[];
  requested_bbox: {
    west: number;
    south: number;
    east: number;
    north: number;
  };
  day_range: number;
  requested_date?: string | null;
  fetched_count: number;
  valid_count: number;
  rejected_count: number;
  upserted_count: number;
  successful_sources: string[];
  failed_sources: string[];
  started_at: string;
  completed_at?: string | null;
  error_summary?: string | null;
}

export interface StoredObservationsResponse {
  mode: string;
  storage: string;
  count: number;
  total: number;
  limit: number;
  offset: number;
  bbox?: {
    west: number;
    south: number;
    east: number;
    north: number;
  } | null;
  observations: ThermalObservation[];
}

export interface FIRMSHotspotsResponse {
  mode: string;
  provider: string;
  sources: string[];
  requested_bbox: {
    west: number;
    south: number;
    east: number;
    north: number;
  };
  day_range: number;
  requested_date?: string | null;
  fetched_at: string;
  data_status: 'fresh' | 'stale';
  count: number;
  rejected_count: number;
  partial: boolean;
  successful_sources: string[];
  failed_sources: string[];
  observations: ThermalObservation[];
}

export interface AnalysisResponse {
  latitude: number;
  longitude: number;
  analysis_timestamp: string;
  nearby_observations_count: number;
  observations: ThermalObservation[];
}

export interface PersistenceProfileResponse {
  observation_id: string;
  analysis_as_of: string;
  radius_m: number;
  algorithm_version: string;
  raw_detection_count_7d: number;
  raw_detection_count_30d: number;
  active_days_7d: number;
  active_days_30d: number;
  active_weeks_30d: number;
  first_seen_30d?: string | null;
  last_seen_30d?: string | null;
  temporal_span_days_30d: number;
  history_coverage_days_7d: number;
  history_coverage_days_30d: number;
  history_coverage_ratio_30d: number;
  persistence_index: number;
  persistence_class: string;
  explanation: string;
  score_components: {
    active_days_score: number;
    temporal_span_score: number;
    multi_week_score: number;
    recency_score: number;
  };
}

export interface BatchPersistenceResponse {
  algorithm_version: string;
  count: number;
  profiles: Record<string, PersistenceProfileResponse>;
}

export interface BackfillResponse {
  status: string;
  days_history: number;
  requested_bbox: Record<string, number>;
  sources: string[];
  chunks_total: number;
  chunks_successful: number;
  chunks_failed: number;
  total_fetched: number;
  total_upserted: number;
  chunk_details: Array<Record<string, unknown>>;
}

export type Hotspot = ThermalObservation;

export interface NearestFeatureDTO {
  osm_uid: string;
  name?: string | null;
  operator?: string | null;
  feature_category: string;
  geometry_quality: string;
  distance_m: number;
  inside_industrial_area: boolean;
}

export interface IndustrialContextProfileResponse {
  observation_id: string;
  radius_m: number;
  context_class: 'STRONG' | 'MODERATE' | 'WEAK' | 'NONE' | 'UNAVAILABLE';
  coverage_status: 'ADEQUATE' | 'PARTIAL' | 'MISSING' | 'FAILED';
  nearest_industrial_distance_m?: number | null;
  nearest_feature?: NearestFeatureDTO | null;
  nearest_flare_distance_m?: number | null;
  nearest_chimney_distance_m?: number | null;
  nearest_refinery_distance_m?: number | null;
  nearest_power_plant_distance_m?: number | null;
  nearest_industrial_area_distance_m?: number | null;
  inside_industrial_area: boolean;
  industrial_feature_count_500m: number;
  industrial_feature_count_1km: number;
  industrial_feature_count_2km: number;
  industrial_feature_count_5km: number;
  has_flare_nearby: boolean;
  has_chimney_nearby: boolean;
  has_refinery_nearby: boolean;
  has_power_plant_nearby: boolean;
  evidence_summary: Record<string, unknown>;
  algorithm_version: string;
  osm_snapshot_at?: string | null;
  calculated_at: string;
}

export interface BatchIndustrialContextResponse {
  total_requested: number;
  profiles: Record<string, IndustrialContextProfileResponse>;
}

export interface OSMFeatureGeoJSON {
  type: 'Feature';
  id: string;
  geometry: {
    type: string;
    coordinates: unknown;
  };
  properties: {
    osm_uid: string;
    name?: string | null;
    operator?: string | null;
    feature_category: string;
    geometry_quality: string;
    thermal_relevance: string;
    tags: Record<string, unknown>;
  };
}

export interface OSMFeatureCollection {
  type: 'FeatureCollection';
  features: OSMFeatureGeoJSON[];
  total_count: number;
}

export type WorldCoverClass =
  | 'TREE_COVER'
  | 'SHRUBLAND'
  | 'GRASSLAND'
  | 'CROPLAND'
  | 'BUILT_UP'
  | 'BARE_SPARSE_VEGETATION'
  | 'SNOW_AND_ICE'
  | 'PERMANENT_WATER'
  | 'HERBACEOUS_WETLAND'
  | 'MANGROVES'
  | 'MOSS_AND_LICHEN'
  | 'UNKNOWN_CODE'
  | 'UNAVAILABLE';

export type LandCoverContextClass =
  | 'TREE_COVER_DOMINANT'
  | 'SHRUBLAND_DOMINANT'
  | 'GRASSLAND_DOMINANT'
  | 'CROPLAND_DOMINANT'
  | 'BUILT_UP_DOMINANT'
  | 'BARE_SPARSE_DOMINANT'
  | 'SNOW_ICE_DOMINANT'
  | 'WATER_DOMINANT'
  | 'WETLAND_DOMINANT'
  | 'MANGROVE_DOMINANT'
  | 'MOSS_LICHEN_DOMINANT'
  | 'MIXED'
  | 'UNAVAILABLE'
  | 'NOT_EVALUATED';

export type LandCoverCoverageStatus = 'COMPLETE' | 'PARTIAL' | 'UNAVAILABLE';

export interface LandCoverProfileResponse {
  observation_id: string;
  provider: string;
  product_name: string;
  product_version: string;
  source_year: number;
  algorithm_version: string;
  point_class_code: number;
  point_class_name: string;
  point_tile_id: string;
  context_class: LandCoverContextClass | string;
  coverage_status: LandCoverCoverageStatus | string;
  dominant_class_250m: string;
  dominant_fraction_250m: number;
  dominant_class_500m: string;
  dominant_fraction_500m: number;
  dominant_class_1000m: string;
  dominant_fraction_1000m: number;
  class_distribution_250m: Record<string, number>;
  class_distribution_500m: Record<string, number>;
  class_distribution_1000m: Record<string, number>;
  valid_pixel_count_250m: number;
  valid_pixel_count_500m: number;
  valid_pixel_count_1000m: number;
  valid_fraction_250m: number;
  valid_fraction_500m: number;
  valid_fraction_1000m: number;
  cropland_fraction_500m: number;
  tree_cover_fraction_500m: number;
  built_up_fraction_500m: number;
  grassland_fraction_500m: number;
  water_fraction_500m: number;
  shrubland_fraction_500m: number;
  wetland_fraction_500m: number;
  bare_sparse_fraction_500m: number;
  mangrove_fraction_500m: number;
  moss_lichen_fraction_500m: number;
  snow_ice_fraction_500m: number;
  tiles_used: string[];
  sampled_at: string;
}

export interface BatchLandCoverResponse {
  total_requested: number;
  count: number;
  profiles: Record<string, LandCoverProfileResponse>;
}

export interface LandCoverSyncResponse {
  status: string;
  total_requested: number;
  cached_profiles_reused: number;
  profiles_computed: number;
  profiles_unavailable: number;
  unique_tiles_required: string[];
  tile_cache_hits: number;
  remote_tile_downloads: number;
  duration_seconds: number;
}

export type SentinelProviderStatus =
  | 'AVAILABLE'
  | 'CLOUD_LIMITED'
  | 'NO_SCENE'
  | 'NOT_EVALUATED'
  | 'RATE_LIMITED'
  | 'PROVIDER_UNAVAILABLE'
  | 'ERROR';

export type SentinelQualityStatus =
  | 'EXCELLENT'
  | 'GOOD'
  | 'LIMITED'
  | 'CLOUD_LIMITED'
  | 'UNAVAILABLE';

export type SentinelTemporalQuality =
  | 'FRESH'
  | 'RECENT'
  | 'OLDER_CONTEXT';

export interface RadiusSpectralStats {
  radius_m: number;
  total_pixel_count: number;
  valid_pixel_count: number;
  valid_fraction: number;
  b04_median?: number | null;
  b08_median?: number | null;
  b11_median?: number | null;
  b12_median?: number | null;
  ndvi_median?: number | null;
  ndmi_median?: number | null;
  nbr_median?: number | null;
  ndvi_p10?: number | null;
  ndvi_p90?: number | null;
  ndmi_p10?: number | null;
  ndmi_p90?: number | null;
  nbr_p10?: number | null;
  nbr_p90?: number | null;
  b11_p90?: number | null;
  b12_p90?: number | null;
}

export interface PointSpectralSample {
  is_valid: boolean;
  scl_code?: number | null;
  b04?: number | null;
  b08?: number | null;
  b11?: number | null;
  b12?: number | null;
  ndvi?: number | null;
  ndmi?: number | null;
  nbr?: number | null;
}

export interface SentinelContextProfileResponse {
  observation_id: string;
  provider: string;
  collection: string;
  scene_id?: string | null;
  product_id?: string | null;
  satellite_platform?: string | null;
  scene_acquisition_time_utc?: string | null;
  target_firms_time_utc?: string | null;
  scene_age_hours?: number | null;
  scene_age_days?: number | null;
  temporal_quality?: SentinelTemporalQuality | null;
  catalogue_cloud_cover?: number | null;
  local_valid_fraction?: number | null;
  local_cloud_fraction?: number | null;
  local_cloud_shadow_fraction?: number | null;
  local_snow_fraction?: number | null;
  quality_status: SentinelQualityStatus;
  provider_status: SentinelProviderStatus;
  analytical_resolution_m: number;
  point_is_valid?: boolean;
  point_scl?: number | null;
  point_b04?: number | null;
  point_b08?: number | null;
  point_b11?: number | null;
  point_b12?: number | null;
  point_ndvi?: number | null;
  point_ndmi?: number | null;
  point_nbr?: number | null;
  stats_100m?: RadiusSpectralStats | null;
  stats_250m?: RadiusSpectralStats | null;
  stats_500m?: RadiusSpectralStats | null;
  algorithm_version: string;
  processed_at?: string | null;
}

export interface BatchSentinelResponse {
  total_requested: number;
  count: number;
  profiles: Record<string, SentinelContextProfileResponse>;
}

export interface SentinelSyncResponse {
  status: string;
  total_requested: number;
  cached_profiles_reused: number;
  profiles_computed: number;
  profiles_cloud_limited: number;
  profiles_no_scene: number;
  profiles_failed: number;
  duration_seconds: number;
  profiles: Record<string, SentinelContextProfileResponse>;
}

export const apiService = {
  async getFIRMSHotspots(params?: {
    west?: number;
    south?: number;
    east?: number;
    north?: number;
    days?: number;
    sources?: string[];
    date?: string;
  }): Promise<FIRMSHotspotsResponse> {
    const response = await apiClient.get<FIRMSHotspotsResponse>('/firms/hotspots', {
      params,
    });
    return response.data;
  },

  async analyzeHotspot(latitude: number, longitude: number): Promise<AnalysisResponse> {
    const response = await apiClient.post<AnalysisResponse>('/analyze', {
      latitude,
      longitude,
    });
    return response.data;
  },

  async syncFIRMS(params?: {
    west?: number;
    south?: number;
    east?: number;
    north?: number;
    days?: number;
    sources?: string[];
    date?: string;
    force_refresh?: boolean;
  }): Promise<FIRMSSyncResponse> {
    const response = await apiClient.post<FIRMSSyncResponse>('/firms/sync', params);
    return response.data;
  },

  async getStoredObservations(params?: {
    west?: number;
    south?: number;
    east?: number;
    north?: number;
    start_time?: string;
    end_time?: string;
    sources?: string;
    limit?: number;
    offset?: number;
  }): Promise<StoredObservationsResponse> {
    const response = await apiClient.get<StoredObservationsResponse>('/observations', {
      params,
    });
    return response.data;
  },

  async getObservationPersistence(observationId: string, radiusM?: number): Promise<PersistenceProfileResponse> {
    const response = await apiClient.get<PersistenceProfileResponse>(`/observations/${observationId}/persistence`, {
      params: radiusM ? { radius_m: radiusM } : undefined,
    });
    return response.data;
  },

  async getBatchPersistence(observationIds: string[], radiusM?: number): Promise<BatchPersistenceResponse> {
    const CHUNK_SIZE = 500;
    if (observationIds.length <= CHUNK_SIZE) {
      const response = await apiClient.post<BatchPersistenceResponse>('/persistence/batch', {
        observation_ids: observationIds,
        radius_m: radiusM,
      });
      return response.data;
    }

    const mergedProfiles: Record<string, PersistenceProfileResponse> = {};
    let algorithmVersion = 'temporal_persistence_v1';

    for (let i = 0; i < observationIds.length; i += CHUNK_SIZE) {
      const chunk = observationIds.slice(i, i + CHUNK_SIZE);
      const response = await apiClient.post<BatchPersistenceResponse>('/persistence/batch', {
        observation_ids: chunk,
        radius_m: radiusM,
      });
      if (response.data?.profiles) {
        Object.assign(mergedProfiles, response.data.profiles);
        if (response.data.algorithm_version) {
          algorithmVersion = response.data.algorithm_version;
        }
      }
    }

    return {
      algorithm_version: algorithmVersion,
      count: Object.keys(mergedProfiles).length,
      profiles: mergedProfiles,
    };
  },

  async getObservationIndustrialContext(observationId: string, radiusM?: number): Promise<IndustrialContextProfileResponse> {
    const response = await apiClient.get<IndustrialContextProfileResponse>(`/observations/${observationId}/industrial-context`, {
      params: radiusM ? { radius_m: radiusM } : undefined,
    });
    return response.data;
  },

  async getBatchIndustrialContext(observationIds: string[]): Promise<BatchIndustrialContextResponse> {
    const CHUNK_SIZE = 500;
    if (observationIds.length <= CHUNK_SIZE) {
      const response = await apiClient.post<BatchIndustrialContextResponse>('/industrial-context/batch', {
        observation_ids: observationIds,
      });
      return response.data;
    }

    const mergedProfiles: Record<string, IndustrialContextProfileResponse> = {};

    for (let i = 0; i < observationIds.length; i += CHUNK_SIZE) {
      const chunk = observationIds.slice(i, i + CHUNK_SIZE);
      const response = await apiClient.post<BatchIndustrialContextResponse>('/industrial-context/batch', {
        observation_ids: chunk,
      });
      if (response.data?.profiles) {
        Object.assign(mergedProfiles, response.data.profiles);
      }
    }

    return {
      total_requested: observationIds.length,
      profiles: mergedProfiles,
    };
  },

  async getOSMIndustrialFeatures(params?: {
    west?: number;
    south?: number;
    east?: number;
    north?: number;
    limit?: number;
  }): Promise<OSMFeatureCollection> {
    const response = await apiClient.get<OSMFeatureCollection>('/osm/industrial/features', {
      params,
    });
    return response.data;
  },

  async syncOSMIndustrial(params: {
    west: number;
    south: number;
    east: number;
    north: number;
    force_refresh?: boolean;
  }): Promise<unknown> {
    const response = await apiClient.post('/osm/industrial/sync', params);
    return response.data;
  },

  async backfillHistory(params?: {
    days_history?: number;
    west?: number;
    south?: number;
    east?: number;
    north?: number;
    sources?: string[];
    chunk_days?: number;
  }): Promise<BackfillResponse> {
    const response = await apiClient.post<BackfillResponse>('/history/backfill', params);
    return response.data;
  },

  async getObservationLandCover(observationId: string): Promise<LandCoverProfileResponse> {
    const response = await apiClient.get<LandCoverProfileResponse>(`/observations/${observationId}/land-cover`);
    return response.data;
  },

  async getBatchLandCover(observationIds: string[]): Promise<BatchLandCoverResponse> {
    const CHUNK_SIZE = 500;
    if (observationIds.length <= CHUNK_SIZE) {
      const response = await apiClient.post<BatchLandCoverResponse>('/land-cover/batch', {
        observation_ids: observationIds,
      });
      return response.data;
    }

    const mergedProfiles: Record<string, LandCoverProfileResponse> = {};

    for (let i = 0; i < observationIds.length; i += CHUNK_SIZE) {
      const chunk = observationIds.slice(i, i + CHUNK_SIZE);
      try {
        const response = await apiClient.post<BatchLandCoverResponse>('/land-cover/batch', {
          observation_ids: chunk,
        });
        if (response.data?.profiles) {
          Object.assign(mergedProfiles, response.data.profiles);
        }
      } catch (chunkErr) {
        console.warn(`[Phase 5 Batch Land Cover] Chunk ${i / CHUNK_SIZE + 1} warning:`, chunkErr);
      }
    }

    return {
      total_requested: observationIds.length,
      count: Object.keys(mergedProfiles).length,
      profiles: mergedProfiles,
    };
  },

  async syncLandCover(params?: {
    observation_ids?: string[];
    limit?: number;
    force_recompute?: boolean;
  }): Promise<LandCoverSyncResponse> {
    const response = await apiClient.post<LandCoverSyncResponse>('/land-cover/sync', params || {});
    return response.data;
  },

  async getObservationSentinelContext(observationId: string): Promise<SentinelContextProfileResponse> {
    const response = await apiClient.get<SentinelContextProfileResponse>(`/observations/${observationId}/sentinel-2`);
    return response.data;
  },

  async getBatchSentinelContext(observationIds: string[]): Promise<BatchSentinelResponse> {
    const CHUNK_SIZE = 500;
    if (observationIds.length <= CHUNK_SIZE) {
      const response = await apiClient.post<BatchSentinelResponse>('/sentinel-2/batch', {
        observation_ids: observationIds,
      });
      return response.data;
    }

    const mergedProfiles: Record<string, SentinelContextProfileResponse> = {};

    for (let i = 0; i < observationIds.length; i += CHUNK_SIZE) {
      const chunk = observationIds.slice(i, i + CHUNK_SIZE);
      try {
        const response = await apiClient.post<BatchSentinelResponse>('/sentinel-2/batch', {
          observation_ids: chunk,
        });
        if (response.data?.profiles) {
          Object.assign(mergedProfiles, response.data.profiles);
        }
      } catch (chunkErr) {
        console.warn(`[Phase 6 Batch Sentinel Context] Chunk ${i / CHUNK_SIZE + 1} warning:`, chunkErr);
      }
    }

    return {
      total_requested: observationIds.length,
      count: Object.keys(mergedProfiles).length,
      profiles: mergedProfiles,
    };
  },

  async syncSentinelContext(params: {
    observation_ids: string[];
    force_refresh?: boolean;
  }): Promise<SentinelSyncResponse> {
    const response = await apiClient.post<SentinelSyncResponse>('/sentinel-2/sync', params);
    return response.data;
  },

  getSentinelPreviewUrl(observationId: string, mode: 'true_color' | 'swir_context'): string {
    return `${API_BASE_URL}/observations/${observationId}/sentinel-2/preview?mode=${mode}`;
  },
};
