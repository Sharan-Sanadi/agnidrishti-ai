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

export type FusionStatus = 'COMPLETE' | 'PARTIAL' | 'NOT_EVALUATED';
export type FusionGroupStatus = 'AVAILABLE' | 'PARTIAL' | 'UNAVAILABLE' | 'CLOUD_LIMITED' | 'NOT_EVALUATED';
export type EvidenceGroupStatus = FusionGroupStatus;

export type FusionFeatureValue = string | number | boolean | null;
export type FusionFeatureVector = Record<string, FusionFeatureValue>;

export interface FusionFeatureSpec {
  name: string;
  group: string;
  source_phase: string;
  source_field: string;
  dtype: string;
  unit: string;
  nullable: boolean;
  model_eligible: boolean;
  description: string;
}

export interface FusionSchemaResponse {
  schema_version: string;
  schema_hash: string;
  total_features: number;
  model_eligible_features: number;
  features: FusionFeatureSpec[];
}
export type FusionSchema = FusionSchemaResponse;

export interface FusionProfileResponse {
  observation_id: string;
  schema_version: string;
  schema_hash: string;
  source_fingerprint: string;
  fusion_status: FusionStatus;
  total_group_count: number;
  evaluated_group_count: number;
  usable_group_count: number;
  expected_feature_count: number;
  non_null_feature_count: number;
  feature_coverage_fraction: number;
  feature_coverage_percent: number;
  feature_vector: FusionFeatureVector;
  group_status: {
    THERMAL: FusionGroupStatus;
    TEMPORAL: FusionGroupStatus;
    INDUSTRIAL: FusionGroupStatus;
    LAND_COVER: FusionGroupStatus;
    SENTINEL: FusionGroupStatus;
  };
  provenance: Record<string, unknown>;
  quality_flags: string[];
  generated_at: string;
  updated_at: string;
}
export type FusionProfile = FusionProfileResponse;

export interface BatchFusionResponse {
  schema_version: string;
  count: number;
  profiles: Record<string, FusionProfileResponse>;
}
export type FusionBatchResponse = BatchFusionResponse;

export interface SyncFusionResponse {
  requested: number;
  created: number;
  updated: number;
  reused: number;
  complete: number;
  partial: number;
  missing_upstream_groups: Record<string, number>;
  duration_ms: number;
  database_queries: number;
}
export type FusionSyncResponse = SyncFusionResponse;

export type ClassificationStatus =
  | 'AVAILABLE'
  | 'INSUFFICIENT_EVIDENCE'
  | 'MODEL_UNAVAILABLE'
  | 'MODEL_INVALID'
  | 'SCHEMA_MISMATCH'
  | 'ERROR';

export type ThermalContextClass =
  | 'INDUSTRIAL_THERMAL_CONTEXT'
  | 'AGRICULTURAL_THERMAL_CONTEXT'
  | 'NATURAL_VEGETATION_THERMAL_CONTEXT'
  | 'BUILT_NON_INDUSTRIAL_CONTEXT'
  | 'MIXED_THERMAL_CONTEXT';

export interface ClassificationPredictionResponse {
  observation_id: string;
  classification_status: ClassificationStatus;
  predicted_class: ThermalContextClass | null;
  class_score: number | null;
  class_probabilities: Record<string, number> | null;
  evidence_coverage: number | null;
  validation_status: string;
  model_version: string;
  fusion_schema_version: string;
  fusion_schema_hash: string;
  fusion_source_fingerprint: string;
  predicted_at: string;
}

export interface BatchClassificationResponse {
  model_version: string;
  count: number;
  predictions: Record<string, ClassificationPredictionResponse>;
}

export interface SyncClassificationResponse {
  requested: number;
  created: number;
  updated: number;
  reused: number;
  available: number;
  insufficient_evidence: number;
  class_distribution: Record<string, number>;
  duration_ms: number;
  database_queries: number;
}

export interface ClassificationModelMetadataResponse {
  model_version: string;
  model_family: string;
  validation_status: string;
  trained_at: string;
  fusion_schema_version: string;
  fusion_schema_hash: string;
  training_dataset_fingerprint: string;
  classes: string[];
  features: string[];
  metrics: {
    macro_f1: number;
    weighted_f1: number;
    balanced_accuracy: number;
    per_class?: Record<string, { precision: number; recall: number; f1_score: number; support: number }>;
    confusion_matrix?: Record<string, Record<string, number>>;
    evaluation_type?: string;
  };
  artifact_hash: string;
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

  async getObservationFusion(observationId: string, schemaVersion: string = 'fusion_v1'): Promise<FusionProfileResponse> {
    const response = await apiClient.get<FusionProfileResponse>(`/observations/${observationId}/fusion`, {
      params: { schema_version: schemaVersion },
    });
    return response.data;
  },

  async getBatchFusion(observationIds: string[], schemaVersion: string = 'fusion_v1'): Promise<BatchFusionResponse> {
    const CHUNK_SIZE = 500;
    if (observationIds.length <= CHUNK_SIZE) {
      const response = await apiClient.post<BatchFusionResponse>('/fusion/batch', {
        observation_ids: observationIds,
        schema_version: schemaVersion,
      });
      return response.data;
    }

    const mergedProfiles: Record<string, FusionProfileResponse> = {};

    for (let i = 0; i < observationIds.length; i += CHUNK_SIZE) {
      const chunk = observationIds.slice(i, i + CHUNK_SIZE);
      try {
        const response = await apiClient.post<BatchFusionResponse>('/fusion/batch', {
          observation_ids: chunk,
          schema_version: schemaVersion,
        });
        if (response.data?.profiles) {
          Object.assign(mergedProfiles, response.data.profiles);
        }
      } catch (chunkErr) {
        console.warn(`[Phase 7 Batch Fusion] Chunk ${i / CHUNK_SIZE + 1} warning:`, chunkErr);
      }
    }

    return {
      schema_version: schemaVersion,
      count: Object.keys(mergedProfiles).length,
      profiles: mergedProfiles,
    };
  },

  async syncFusion(params: {
    observation_ids: string[];
    force_recompute?: boolean;
  }): Promise<SyncFusionResponse> {
    const CHUNK_SIZE = 500;
    const observationIds = params.observation_ids;

    if (observationIds.length <= CHUNK_SIZE) {
      const response = await apiClient.post<SyncFusionResponse>('/fusion/sync', params);
      return response.data;
    }

    let created = 0;
    let updated = 0;
    let reused = 0;
    let complete = 0;
    let partial = 0;
    let duration_ms = 0;
    let database_queries = 0;
    const missing: Record<string, number> = {};

    for (let i = 0; i < observationIds.length; i += CHUNK_SIZE) {
      const chunk = observationIds.slice(i, i + CHUNK_SIZE);
      try {
        const response = await apiClient.post<SyncFusionResponse>('/fusion/sync', {
          observation_ids: chunk,
          force_recompute: params.force_recompute,
        });
        const d = response.data;
        created += d.created;
        updated += d.updated;
        reused += d.reused;
        complete += d.complete;
        partial += d.partial;
        duration_ms += d.duration_ms;
        database_queries += d.database_queries;
        if (d.missing_upstream_groups) {
          for (const [k, v] of Object.entries(d.missing_upstream_groups)) {
            missing[k] = (missing[k] || 0) + v;
          }
        }
      } catch (chunkErr) {
        console.warn(`[Phase 7 Sync Fusion] Chunk ${i / CHUNK_SIZE + 1} warning:`, chunkErr);
      }
    }

    return {
      requested: observationIds.length,
      created,
      updated,
      reused,
      complete,
      partial,
      missing_upstream_groups: missing,
      duration_ms: Math.round(duration_ms * 100) / 100,
      database_queries,
    };
  },

  async getFusionSchema(): Promise<FusionSchemaResponse> {
    const response = await apiClient.get<FusionSchemaResponse>('/fusion/schema');
    return response.data;
  },

  async getObservationClassification(observationId: string): Promise<ClassificationPredictionResponse> {
    const response = await apiClient.get<ClassificationPredictionResponse>(`/observations/${observationId}/classification`);
    return response.data;
  },

  async getBatchClassifications(
    observationIds: string[],
    modelVersion: string = 'agnidrishti_context_classifier_v1'
  ): Promise<BatchClassificationResponse> {
    const CHUNK_SIZE = 500;

    if (observationIds.length <= CHUNK_SIZE) {
      const response = await apiClient.post<BatchClassificationResponse>('/classification/batch', {
        observation_ids: observationIds,
        model_version: modelVersion,
      });
      return response.data;
    }

    const mergedPredictions: Record<string, ClassificationPredictionResponse> = {};

    for (let i = 0; i < observationIds.length; i += CHUNK_SIZE) {
      const chunk = observationIds.slice(i, i + CHUNK_SIZE);
      try {
        const response = await apiClient.post<BatchClassificationResponse>('/classification/batch', {
          observation_ids: chunk,
          model_version: modelVersion,
        });
        if (response.data?.predictions) {
          Object.assign(mergedPredictions, response.data.predictions);
        }
      } catch (chunkErr) {
        console.warn(`[Phase 8 Batch Classification] Chunk ${i / CHUNK_SIZE + 1} warning:`, chunkErr);
      }
    }

    return {
      model_version: modelVersion,
      count: Object.keys(mergedPredictions).length,
      predictions: mergedPredictions,
    };
  },

  async syncClassifications(params: {
    observation_ids: string[];
    force_recompute?: boolean;
  }): Promise<SyncClassificationResponse> {
    const CHUNK_SIZE = 500;
    const observationIds = params.observation_ids;

    if (observationIds.length <= CHUNK_SIZE) {
      const response = await apiClient.post<SyncClassificationResponse>('/classification/sync', params);
      return response.data;
    }

    let created = 0;
    let updated = 0;
    let reused = 0;
    let available = 0;
    let insufficient = 0;
    let duration_ms = 0;
    let database_queries = 0;
    const classDist: Record<string, number> = {};

    for (let i = 0; i < observationIds.length; i += CHUNK_SIZE) {
      const chunk = observationIds.slice(i, i + CHUNK_SIZE);
      try {
        const response = await apiClient.post<SyncClassificationResponse>('/classification/sync', {
          observation_ids: chunk,
          force_recompute: params.force_recompute,
        });
        const d = response.data;
        created += d.created;
        updated += d.updated;
        reused += d.reused;
        available += d.available;
        insufficient += d.insufficient_evidence;
        duration_ms += d.duration_ms;
        database_queries += d.database_queries;
        if (d.class_distribution) {
          for (const [k, v] of Object.entries(d.class_distribution)) {
            classDist[k] = (classDist[k] || 0) + v;
          }
        }
      } catch (chunkErr) {
        console.warn(`[Phase 8 Sync Classification] Chunk ${i / CHUNK_SIZE + 1} warning:`, chunkErr);
      }
    }

    return {
      requested: observationIds.length,
      created,
      updated,
      reused,
      available,
      insufficient_evidence: insufficient,
      class_distribution: classDist,
      duration_ms: Math.round(duration_ms * 100) / 100,
      database_queries,
    };
  },

  async getClassificationModelMetadata(): Promise<ClassificationModelMetadataResponse> {
    const response = await apiClient.get<ClassificationModelMetadataResponse>('/classification/model');
    return response.data;
  },

  // ---------------------------------------------------------------------------
  // Phase 9: Model Explainability Engine
  // ---------------------------------------------------------------------------

  async getObservationExplanation(observationId: string): Promise<LocalExplanationResponse> {
    const response = await apiClient.get<LocalExplanationResponse>(`/observations/${observationId}/explanation`);
    return response.data;
  },

  async getBatchExplanations(observationIds: string[]): Promise<BatchExplanationResponse> {
    const CHUNK_SIZE = 500;

    if (observationIds.length <= CHUNK_SIZE) {
      const response = await apiClient.post<BatchExplanationResponse>('/explanations/batch', {
        observation_ids: observationIds,
      });
      return response.data;
    }

    const mergedExplanations: Record<string, LocalExplanationResponse> = {};

    for (let i = 0; i < observationIds.length; i += CHUNK_SIZE) {
      const chunk = observationIds.slice(i, i + CHUNK_SIZE);
      try {
        const response = await apiClient.post<BatchExplanationResponse>('/explanations/batch', {
          observation_ids: chunk,
        });
        if (response.data?.explanations) {
          Object.assign(mergedExplanations, response.data.explanations);
        }
      } catch (chunkErr) {
        console.warn(`[Phase 9 Batch Explanations] Chunk ${i / CHUNK_SIZE + 1} warning:`, chunkErr);
      }
    }

    return {
      explanation_version: 'agnidrishti_explainer_v1',
      count: Object.keys(mergedExplanations).length,
      explanations: mergedExplanations,
    };
  },

  async syncExplanations(params: {
    observation_ids: string[];
    force_recompute?: boolean;
  }): Promise<SyncExplanationResponse> {
    const CHUNK_SIZE = 500;
    const observationIds = params.observation_ids;

    if (observationIds.length <= CHUNK_SIZE) {
      const response = await apiClient.post<SyncExplanationResponse>('/explanations/sync', params);
      return response.data;
    }

    let created = 0;
    let updated = 0;
    let reused = 0;
    let available = 0;
    let insufficient = 0;
    let duration_ms = 0;
    let database_queries = 0;

    for (let i = 0; i < observationIds.length; i += CHUNK_SIZE) {
      const chunk = observationIds.slice(i, i + CHUNK_SIZE);
      try {
        const response = await apiClient.post<SyncExplanationResponse>('/explanations/sync', {
          observation_ids: chunk,
          force_recompute: params.force_recompute,
        });
        const d = response.data;
        created += d.created;
        updated += d.updated;
        reused += d.reused;
        available += d.available;
        insufficient += d.insufficient_evidence;
        duration_ms += d.duration_ms;
        database_queries += d.database_queries;
      } catch (chunkErr) {
        console.warn(`[Phase 9 Sync Explanation] Chunk ${i / CHUNK_SIZE + 1} warning:`, chunkErr);
      }
    }

    return {
      requested: observationIds.length,
      created,
      updated,
      reused,
      available,
      insufficient_evidence: insufficient,
      duration_ms: Math.round(duration_ms * 100) / 100,
      database_queries,
    };
  },

  async getGlobalExplanation(): Promise<GlobalExplanationResponse> {
    const response = await apiClient.get<GlobalExplanationResponse>('/explanations/global');
    return response.data;
  },
};

// -----------------------------------------------------------------------------
// Phase 9 TypeScript Interfaces
// -----------------------------------------------------------------------------

export interface FeatureContributionItem {
  feature_name: string;
  display_name: string;
  feature_group: string;
  raw_value: string | number | boolean | null;
  display_value: string;
  unit: string;
  contribution: number;
  relative_strength: number;
  direction: 'SUPPORTS' | 'OPPOSES' | 'NEUTRAL' | string;
  rank: number;
}

export interface GroupContributionItem {
  group: string;
  total_contribution: number;
  relative_strength: number;
  direction: 'SUPPORTS' | 'OPPOSES' | 'NEUTRAL' | string;
  contribution_level: 'HIGH_CONTRIBUTION' | 'MEDIUM_CONTRIBUTION' | 'LOW_CONTRIBUTION' | string;
  feature_count: number;
}

export interface LocalExplanationResponse {
  observation_id: string;
  explanation_status: 'AVAILABLE' | 'INSUFFICIENT_EVIDENCE' | string;
  predicted_class?: string | null;
  prediction_score?: number | null;
  model_version: string;
  validation_status: string;
  explanation_version: string;
  method: string;
  feature_coverage?: number | null;
  base_value?: number | null;
  explained_output?: number | null;
  additivity_error?: number | null;
  top_supporting_features: FeatureContributionItem[];
  top_opposing_features: FeatureContributionItem[];
  group_contributions: Record<string, GroupContributionItem>;
  quality_flags: string[];
  generated_at: string;
}

export interface BatchExplanationResponse {
  explanation_version: string;
  count: number;
  explanations: Record<string, LocalExplanationResponse>;
}

export interface SyncExplanationResponse {
  requested: number;
  created: number;
  updated: number;
  reused: number;
  available: number;
  insufficient_evidence: number;
  duration_ms: number;
  database_queries: number;
}

export interface GlobalFeatureImportanceItem {
  feature_name: string;
  display_name: string;
  feature_group: string;
  importance_mean: number;
  importance_std: number;
  rank: number;
}

export interface GlobalExplanationResponse {
  model_version: string;
  explanation_version: string;
  validation_status: string;
  scoring_metric: string;
  dataset_fingerprint: string;
  top_features: GlobalFeatureImportanceItem[];
  feature_groups: Record<string, number>;
  computed_at: string;
  random_seed: number;
  evaluation_split: string;
  evaluation_samples?: number;
}
