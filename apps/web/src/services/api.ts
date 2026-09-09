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
  }
};
