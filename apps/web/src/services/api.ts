import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Hotspot {
  id: string;
  latitude: number;
  longitude: number;
  acquired_at: string;
  source: string;
  satellite?: string;
  frp_mw: number;
  brightness_ti4: number;
  brightness_ti5: number;
  confidence: string;
  day_night: string;
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

  async analyzeHotspot(latitude: number, longitude: number): Promise<AnalysisResponse> {
    const response = await apiClient.post<AnalysisResponse>('/analyze', {
      latitude,
      longitude,
    });
    return response.data;
  }
};
