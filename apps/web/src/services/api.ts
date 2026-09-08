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

export interface Hotspot {
  id: string;
  latitude: number;
  longitude: number;
  acquired_at: string;
  source: string;
  satellite?: string;
  instrument?: string;
  frp_mw?: number | null;
  brightness_ti4?: number | null;
  brightness_ti5?: number | null;
  confidence: string;
  confidence_normalized?: string | null;
  day_night?: string | null;
  scan?: number | null;
  track?: number | null;
  firms_version?: string | null;
  ingestion_time_utc?: string;
  first_ingested_at?: string;
  last_seen_at?: string;
  ingestion_count?: number;
  stored_in_postgis?: boolean;
  risk?: string;
  persistent?: boolean;
  classification?: string;
  is_live_firms?: boolean;
}

export interface HotspotListResponse {
  hotspots: Hotspot[];
  total: number;
  analysis_mode: string;
}

export interface EvidenceItem {
  type: string;
  label: string;
  value: number | string;
  unit?: string;
  weight_or_importance?: number;
}

export interface AnalysisResponse {
  hotspot: Hotspot;
  thermal_context: Record<string, unknown>;
  temporal_context: Record<string, unknown>;
  industrial_context: {
    industrial_zone?: boolean;
    industrial_facilities_500m?: number;
    distance_to_nearest_m?: number;
    infrastructure_types?: string[];
  };
  landcover_context: {
    dominant_class?: string;
    built_area_ratio?: number;
    vegetation_ratio?: number;
    source?: string;
  };
  satellite_context: Record<string, unknown>;
  classification: {
    top_level_class: string;
    subclass: string;
    confidence: number;
    reasoning_summary: string;
    evidence: EvidenceItem[];
    model_version: string;
    requires_ground_verification: boolean;
  };
  anomaly_score: number;
  warnings: string[];
  data_sources: Array<Record<string, unknown>>;
  data_quality: Record<string, unknown>;
  analysis_mode: string;
}

export const api = {
  async getHotspots(): Promise<HotspotListResponse> {
    const response = await apiClient.get<HotspotListResponse>('/hotspots');
    return response.data;
  },

  async getFIRMSHotspots(params?: {
    west?: number;
    south?: number;
    east?: number;
    north?: number;
    days?: number;
    sources?: string;
    date?: string;
    force_refresh?: boolean;
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

    // Chunk into bounded batches of 500 and merge
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
