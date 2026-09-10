import { useState } from 'react';
import {
  X,
  Satellite,
  Flame,
  Clock,
  Compass,
  Hash,
  Database,
  History,
  Factory,
  Building2,
  MapPin,
  Trees,
  Layers,
  BrainCircuit,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Scale,
  CheckCircle2,
} from 'lucide-react';
import {
  AnalysisResponse,
  ThermalObservation,
  PersistenceProfileResponse,
  IndustrialContextProfileResponse,
  LandCoverProfileResponse,
  SentinelContextProfileResponse,
  FusionProfileResponse,
  ClassificationPredictionResponse,
  LocalExplanationResponse,
  apiService,
} from '../services/api';

interface AnalysisDrawerProps {
  hotspot: ThermalObservation | null;
  analysis?: AnalysisResponse | null;
  persistenceProfile?: PersistenceProfileResponse | null;
  industrialContextProfile?: IndustrialContextProfileResponse | null;
  landCoverProfile?: LandCoverProfileResponse | null;
  sentinelProfile?: SentinelContextProfileResponse | null;
  fusionProfile?: FusionProfileResponse | null;
  classificationProfile?: ClassificationPredictionResponse | null;
  explanationProfile?: LocalExplanationResponse | null;
  loading?: boolean;
  onClose: () => void;
  onSyncSentinel?: (observationId: string) => Promise<void>;
  onSyncExplanation?: (observationId: string) => Promise<void>;
}

export function AnalysisDrawer({
  hotspot,
  persistenceProfile,
  industrialContextProfile,
  landCoverProfile,
  sentinelProfile,
  fusionProfile,
  classificationProfile,
  explanationProfile,
  onClose,
  onSyncSentinel,
  onSyncExplanation,
}: AnalysisDrawerProps) {
  const [previewMode, setPreviewMode] = useState<'true_color' | 'swir_context'>('true_color');

  if (!hotspot) return null;

  const conf = (hotspot.confidence || '').toLowerCase();
  const confLabel = conf === 'h' ? 'High' : conf === 'n' ? 'Nominal' : conf === 'l' ? 'Low' : hotspot.confidence;
  const dayNightLabel = hotspot.daynight === 'D' ? 'Day (D)' : hotspot.daynight === 'N' ? 'Night (N)' : (hotspot.daynight || 'N/A');

  return (
    <div className="absolute top-0 right-0 h-full w-96 md:w-[420px] bg-white shadow-2xl z-[1000] flex flex-col transform transition-transform duration-300 ease-in-out border-l border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-slate-900 text-white">
        <div className="flex items-center gap-2">
          <Satellite size={20} className="text-orange-400" />
          <h2 className="text-sm font-bold tracking-wide uppercase">
            NASA FIRMS Observation
          </h2>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded-full transition-colors text-slate-300">
          <X size={18} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Primary Observation Card */}
        <div className="bg-orange-50/70 rounded-lg p-4 border border-orange-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-orange-800 uppercase tracking-wider flex items-center gap-1">
              <Flame size={14} className="text-orange-600" /> Thermal Detection
            </span>
            <span className="bg-orange-100 text-orange-900 border border-orange-300 text-xs font-semibold px-2 py-0.5 rounded">
              {confLabel} Confidence
            </span>
          </div>
          <p className="text-2xl font-black text-slate-900">
            {hotspot.frp != null ? `${hotspot.frp} MW` : 'FRP Available'}
          </p>
          <p className="text-xs text-slate-600 mt-1">
            Fire Radiative Power (MW) measured by VIIRS sensor
          </p>

          <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-orange-200/80 text-xs">
            <div>
              <span className="text-slate-500 font-medium block">Brightness (TI4)</span>
              <span className="font-bold text-slate-900 text-sm">
                {hotspot.bright_ti4 != null ? `${hotspot.bright_ti4} K` : 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 font-medium block">Brightness (TI5)</span>
              <span className="font-bold text-slate-900 text-sm">
                {hotspot.bright_ti5 != null ? `${hotspot.bright_ti5} K` : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Satellite & Sensor Telemetry */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Satellite Telemetry</h3>

          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 text-xs space-y-2.5">
            <div className="flex justify-between items-center border-b border-slate-200 pb-2">
              <span className="text-slate-500">Platform / Instrument</span>
              <span className="font-semibold text-slate-900">{hotspot.satellite || 'VIIRS'} ({hotspot.instrument || 'VIIRS'})</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-200 pb-2">
              <span className="text-slate-500">Source Feed</span>
              <span className="font-semibold text-slate-900">{hotspot.source}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-200 pb-2">
              <span className="text-slate-500">Solar Cycle</span>
              <span className="font-semibold text-slate-900">{dayNightLabel}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500">Pixel Resolution</span>
              <span className="font-semibold text-slate-900">
                {hotspot.scan != null && hotspot.track != null ? `${hotspot.scan} × ${hotspot.track} km` : '375m nominal'}
              </span>
            </div>
          </div>
        </div>

        {/* Spatial & Temporal Provenance */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Spatial & Temporal Provenance</h3>
          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 text-xs space-y-2.5">
            <div className="flex items-start gap-2">
              <Compass size={15} className="text-blue-600 mt-0.5 shrink-0" />
              <div>
                <span className="text-slate-500 block">WGS84 Coordinates</span>
                <span className="font-mono font-semibold text-slate-900">
                  {hotspot.latitude.toFixed(5)}° N, {hotspot.longitude.toFixed(5)}° E
                </span>
              </div>
            </div>

            <div className="flex items-start gap-2 pt-2 border-t border-slate-200">
              <Clock size={15} className="text-green-600 mt-0.5 shrink-0" />
              <div>
                <span className="text-slate-500 block">Satellite Acquisition (UTC)</span>
                <span className="font-mono font-semibold text-slate-900">
                  {new Date(hotspot.acquisition_time_utc).toISOString()}
                </span>
              </div>
            </div>

            <div className="flex items-start gap-2 pt-2 border-t border-slate-200">
              <Hash size={15} className="text-purple-600 mt-0.5 shrink-0" />
              <div>
                <span className="text-slate-500 block">Deterministic ID</span>
                <span className="font-mono text-[11px] text-slate-800 break-all">
                  {hotspot.id}
                </span>
              </div>
            </div>

            {hotspot.stored_in_postgis && (
              <div className="pt-2 border-t border-slate-200 space-y-1.5">
                <div className="flex items-center gap-1.5 text-emerald-700 font-bold">
                  <Database size={14} className="text-emerald-600" />
                  <span>Stored in PostGIS (SRID: 4326)</span>
                </div>
                {hotspot.first_ingested_at && (
                  <div className="flex justify-between text-[11px] text-slate-600">
                    <span>First Ingested:</span>
                    <span className="font-mono font-medium text-slate-800">
                      {new Date(hotspot.first_ingested_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} UTC
                    </span>
                  </div>
                )}
                {hotspot.last_seen_at && (
                  <div className="flex justify-between text-[11px] text-slate-600">
                    <span>Last Seen:</span>
                    <span className="font-mono font-medium text-slate-800">
                      {new Date(hotspot.last_seen_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} UTC
                    </span>
                  </div>
                )}
                {hotspot.ingestion_count != null && (
                  <div className="flex justify-between text-[11px] text-slate-600">
                    <span>Ingestion Count:</span>
                    <span className="font-bold text-slate-900">{hotspot.ingestion_count}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Phase 3 Temporal Persistence Panel */}
        {persistenceProfile && (
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <History size={14} className="text-purple-600" /> Temporal Persistence (Phase 3)
            </h3>
            <div className="bg-purple-50/70 rounded-lg p-3.5 border border-purple-200 text-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className={`text-xs font-black px-2.5 py-1 rounded uppercase tracking-wider border ${
                  persistenceProfile.persistence_class === 'PERSISTENT'
                    ? 'bg-purple-600 text-white border-purple-700'
                    : persistenceProfile.persistence_class === 'RECURRING'
                    ? 'bg-amber-600 text-white border-amber-700'
                    : persistenceProfile.persistence_class === 'OCCASIONAL'
                    ? 'bg-blue-600 text-white border-blue-700'
                    : persistenceProfile.persistence_class === 'ISOLATED'
                    ? 'bg-slate-700 text-white border-slate-800'
                    : 'bg-gray-200 text-gray-800 border-gray-300'
                }`}>
                  {persistenceProfile.persistence_class.replace(/_/g, ' ')}
                </span>
                <div className="text-right">
                  <span className="text-[10px] text-purple-700 font-bold block">Persistence Index</span>
                  <span className="text-lg font-black text-purple-950">
                    {persistenceProfile.persistence_class === 'INSUFFICIENT_HISTORY'
                      ? 'N/A'
                      : `${persistenceProfile.persistence_index} / 100`}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-purple-200/80">
                <div>
                  <span className="text-slate-500 block text-[11px]">Active Days (30d)</span>
                  <span className="font-bold text-slate-900 text-sm">{persistenceProfile.active_days_30d} days</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[11px]">Active Days (7d)</span>
                  <span className="font-bold text-slate-900 text-sm">{persistenceProfile.active_days_7d} days</span>
                </div>
              </div>

              <div className="pt-2 border-t border-purple-200/80 text-[11px] text-purple-900 leading-relaxed bg-white/60 p-2.5 rounded border border-purple-100">
                <p className="font-medium">{persistenceProfile.explanation}</p>
              </div>
            </div>
          </div>
        )}

        {/* Phase 4 Industrial Context Panel (OSM) */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Factory size={14} className="text-cyan-600" /> Industrial Context (Phase 4 — OSM)
          </h3>

          {industrialContextProfile ? (
            <div className="bg-cyan-50/70 rounded-lg p-3.5 border border-cyan-200 text-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className={`text-xs font-black px-2.5 py-1 rounded uppercase tracking-wider border ${
                  industrialContextProfile.context_class === 'STRONG'
                    ? 'bg-cyan-700 text-white border-cyan-800'
                    : industrialContextProfile.context_class === 'MODERATE'
                    ? 'bg-sky-600 text-white border-sky-700'
                    : industrialContextProfile.context_class === 'WEAK'
                    ? 'bg-teal-600 text-white border-teal-700'
                    : industrialContextProfile.context_class === 'NONE'
                    ? 'bg-slate-600 text-white border-slate-700'
                    : 'bg-amber-600 text-white border-amber-700'
                }`}>
                  {industrialContextProfile.context_class} INDUSTRIAL CONTEXT
                </span>
                <span className="text-[10px] font-bold text-slate-500">
                  Radius: {industrialContextProfile.radius_m}m
                </span>
              </div>

              {industrialContextProfile.context_class === 'UNAVAILABLE' ? (
                <div className="bg-amber-100/70 p-2.5 rounded border border-amber-300 text-amber-900 text-xs">
                  <p className="font-bold mb-1">INDUSTRIAL CONTEXT UNAVAILABLE</p>
                  <p className="text-[11px]">
                    Spatial OpenStreetMap coverage for this 5km envelope is missing or pending sync. Click &quot;Sync OSM&quot; on dashboard to fetch real mapped infrastructure.
                  </p>
                </div>
              ) : industrialContextProfile.context_class === 'NONE' ? (
                <div className="bg-slate-100 p-2.5 rounded border border-slate-300 text-slate-800 text-xs">
                  <p className="font-bold mb-1">NO MAPPED INDUSTRIAL CONTEXT</p>
                  <p className="text-[11px]">
                    Complete 5km OSM coverage evaluated. Zero mapped industrial infrastructure features found within 5,000m envelope.
                  </p>
                </div>
              ) : (
                <>
                  {/* Nearest Feature Card */}
                  {industrialContextProfile.nearest_feature && (
                    <div className="bg-white p-3 rounded border border-cyan-200 space-y-1.5 shadow-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900 flex items-center gap-1.5 text-sm">
                          <Building2 size={15} className="text-cyan-600" />
                          {industrialContextProfile.nearest_feature.name || industrialContextProfile.nearest_feature.osm_uid}
                        </span>
                        <span className="font-mono text-cyan-700 font-extrabold text-xs">
                          {industrialContextProfile.nearest_feature.distance_m}m
                        </span>
                      </div>
                      <div className="flex justify-between text-[11px] text-slate-600 pt-1 border-t border-slate-100">
                        <span>Category: <strong className="text-slate-800">{industrialContextProfile.nearest_feature.feature_category}</strong></span>
                        <span>Quality: <strong className="text-slate-800">{industrialContextProfile.nearest_feature.geometry_quality}</strong></span>
                      </div>
                      {industrialContextProfile.inside_industrial_area && (
                        <div className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 mt-1 inline-block">
                          Inside Mapped Industrial Area (ST_Covers = true)
                        </div>
                      )}
                    </div>
                  )}

                  {/* Feature Breakdown Counts */}
                  <div className="grid grid-cols-4 gap-1.5 text-center pt-1 text-[11px]">
                    <div className="bg-white p-2 rounded border border-cyan-100">
                      <span className="text-slate-400 block text-[9px] uppercase">500m</span>
                      <span className="font-bold text-slate-900">{industrialContextProfile.industrial_feature_count_500m}</span>
                    </div>
                    <div className="bg-white p-2 rounded border border-cyan-100">
                      <span className="text-slate-400 block text-[9px] uppercase">1km</span>
                      <span className="font-bold text-slate-900">{industrialContextProfile.industrial_feature_count_1km}</span>
                    </div>
                    <div className="bg-white p-2 rounded border border-cyan-100">
                      <span className="text-slate-400 block text-[9px] uppercase">2km</span>
                      <span className="font-bold text-slate-900">{industrialContextProfile.industrial_feature_count_2km}</span>
                    </div>
                    <div className="bg-white p-2 rounded border border-cyan-100">
                      <span className="text-slate-400 block text-[9px] uppercase">5km</span>
                      <span className="font-bold text-slate-900">{industrialContextProfile.industrial_feature_count_5km}</span>
                    </div>
                  </div>
                </>
              )}

              {/* OpenStreetMap Attribution & Scientific Disclaimer */}
              <div className="pt-2 border-t border-cyan-200 text-[10px] text-slate-500 space-y-1">
                <p className="flex items-center gap-1 font-semibold text-slate-600">
                  <MapPin size={12} className="text-cyan-600" /> ©️ OpenStreetMap contributors
                </p>
                <p className="leading-tight text-[9.5px]">
                  OpenStreetMap is community-maintained and may be incomplete. Absence of mapped industrial infrastructure does not prove absence of real-world industrial infrastructure.
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 text-xs text-slate-600">
              Evaluating PostGIS metric distance to OpenStreetMap industrial infrastructure...
            </div>
          )}
        </div>

        {/* Phase 5 Land-Cover Context Panel (ESA WorldCover) */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Trees size={14} className="text-emerald-600" /> Land-Cover Context (Phase 5 — ESA WorldCover)
          </h3>

          {landCoverProfile ? (
            <div className="bg-emerald-50/70 rounded-lg p-3.5 border border-emerald-200 text-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className={`text-xs font-black px-2.5 py-1 rounded uppercase tracking-wider border ${
                  landCoverProfile.context_class.includes('CROPLAND')
                    ? 'bg-amber-700 text-white border-amber-800'
                    : landCoverProfile.context_class.includes('TREE_COVER')
                    ? 'bg-emerald-800 text-white border-emerald-900'
                    : landCoverProfile.context_class.includes('BUILT_UP')
                    ? 'bg-rose-700 text-white border-rose-800'
                    : landCoverProfile.context_class.includes('GRASSLAND')
                    ? 'bg-lime-700 text-white border-lime-800'
                    : landCoverProfile.context_class.includes('MIXED')
                    ? 'bg-slate-700 text-white border-slate-800'
                    : 'bg-gray-600 text-white border-gray-700'
                }`}>
                  {landCoverProfile.context_class.replace(/_/g, ' ')}
                </span>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                  landCoverProfile.coverage_status === 'COMPLETE'
                    ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                    : landCoverProfile.coverage_status === 'PARTIAL'
                    ? 'bg-amber-100 text-amber-800 border-amber-300'
                    : 'bg-red-100 text-red-800 border-red-300'
                }`}>
                  {landCoverProfile.coverage_status} COVERAGE
                </span>
              </div>

              {/* Point Pixel Classification */}
              <div className="bg-white p-3 rounded border border-emerald-200 space-y-1 shadow-sm">
                <div className="flex justify-between items-center">
                  <span className="text-slate-500 text-[11px]">Point Pixel (Exact Coordinate):</span>
                  <span className="font-bold text-slate-900 text-xs flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
                    {landCoverProfile.point_class_name.replace(/_/g, ' ')} ({landCoverProfile.point_class_code})
                  </span>
                </div>
                <div className="flex justify-between items-center text-[10px] text-slate-500 pt-1 border-t border-slate-100">
                  <span>Source Tile:</span>
                  <span className="font-mono font-medium text-slate-700">{landCoverProfile.point_tile_id}</span>
                </div>
              </div>

              {/* Multi-Scale Neighborhood Dominance */}
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                  Multi-Scale Neighborhood Dominance
                </span>
                <div className="grid grid-cols-3 gap-1.5 text-center text-[11px]">
                  <div className="bg-white p-2 rounded border border-emerald-100">
                    <span className="text-slate-400 block text-[9px] uppercase font-semibold">250m Dominant</span>
                    <span className="font-bold text-slate-900 block truncate">
                      {landCoverProfile.dominant_class_250m.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[10px] text-emerald-700 font-bold">
                      {(landCoverProfile.dominant_fraction_250m * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="bg-white p-2 rounded border border-emerald-100">
                    <span className="text-slate-400 block text-[9px] uppercase font-semibold">500m Dominant</span>
                    <span className="font-bold text-slate-900 block truncate">
                      {landCoverProfile.dominant_class_500m.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[10px] text-emerald-700 font-bold">
                      {(landCoverProfile.dominant_fraction_500m * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="bg-white p-2 rounded border border-emerald-100">
                    <span className="text-slate-400 block text-[9px] uppercase font-semibold">1km Dominant</span>
                    <span className="font-bold text-slate-900 block truncate">
                      {landCoverProfile.dominant_class_1000m.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[10px] text-emerald-700 font-bold">
                      {(landCoverProfile.dominant_fraction_1000m * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* 500m Composition Breakdown (Sorted Descending) */}
              <div className="space-y-1.5 pt-1">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                    500m Land-Cover Composition
                  </span>
                  <span className="text-[10px] text-slate-400">
                    {landCoverProfile.valid_pixel_count_500m} valid px ({(landCoverProfile.valid_fraction_500m * 100).toFixed(0)}%)
                  </span>
                </div>
                <div className="bg-white rounded border border-emerald-200 overflow-hidden divide-y divide-slate-100">
                  {Object.entries(landCoverProfile.class_distribution_500m || {})
                    .filter(([, frac]) => frac > 0.005)
                    .sort((a, b) => b[1] - a[1])
                    .map(([cls, frac]) => (
                      <div key={cls} className="flex items-center justify-between px-2.5 py-1.5 text-[11px]">
                        <span className="font-medium text-slate-700">{cls.replace(/_/g, ' ')}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-emerald-600 h-full rounded-full"
                              style={{ width: `${Math.min(100, Math.round(frac * 100))}%` }}
                            />
                          </div>
                          <span className="font-mono font-bold text-slate-900 w-10 text-right">
                            {(frac * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>

              {/* Attribution & Scientific Disclaimer */}
              <div className="pt-2 border-t border-emerald-200 text-[10px] text-slate-500 space-y-1">
                <p className="font-semibold text-slate-600">
                  Source: {landCoverProfile.product_name} {landCoverProfile.product_version} (~10m)
                </p>
                <p className="text-[9.5px] leading-tight text-slate-500">
                  ©️ ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium
                </p>
                <p className="leading-tight text-[9px] text-amber-800/80 bg-amber-50 p-1.5 rounded border border-amber-200/60">
                  Notice: ESA WorldCover 2021 baseline reflects 2021 physical land cover (~10m). Land-cover context does NOT confirm fire cause (e.g. Cropland ≠ confirmed agricultural fire).
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 text-xs text-slate-600">
              Evaluating ESA WorldCover 10m 2021 v200 raster pixel context...
            </div>
          )}
        </div>

        {/* Phase 6: Sentinel-2 Optical/SWIR Satellite Context */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <Satellite size={14} className="text-indigo-600" /> Sentinel-2 Context — Phase 6
            </h3>
            {sentinelProfile?.quality_status && (
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${
                  sentinelProfile.quality_status === 'EXCELLENT'
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                    : sentinelProfile.quality_status === 'GOOD'
                    ? 'bg-blue-50 text-blue-800 border-blue-300'
                    : sentinelProfile.quality_status === 'LIMITED'
                    ? 'bg-amber-50 text-amber-800 border-amber-300'
                    : sentinelProfile.quality_status === 'CLOUD_LIMITED'
                    ? 'bg-orange-50 text-orange-800 border-orange-300'
                    : 'bg-slate-100 text-slate-700 border-slate-300'
                }`}
              >
                {sentinelProfile.quality_status.replace(/_/g, ' ')}
              </span>
            )}
          </div>

          {sentinelProfile && (sentinelProfile.provider_status === 'AVAILABLE' || sentinelProfile.provider_status === 'CLOUD_LIMITED') ? (
            <div className="bg-indigo-50/50 rounded-lg p-3.5 border border-indigo-200 text-xs space-y-3.5">
              {/* Scene Age & Temporal Banner */}
              <div className="flex items-center justify-between bg-white p-2.5 rounded border border-indigo-100">
                <div>
                  <span className="text-slate-400 block text-[9px] uppercase font-semibold">Scene Acquisition</span>
                  <span className="font-bold text-slate-900 block text-xs">
                    {sentinelProfile.scene_age_hours != null
                      ? sentinelProfile.scene_age_hours < 24
                        ? `${sentinelProfile.scene_age_hours.toFixed(1)}h before FIRMS`
                        : `${(sentinelProfile.scene_age_hours / 24).toFixed(1)}d before FIRMS`
                      : 'Prior to FIRMS'}
                  </span>
                </div>
                {sentinelProfile.temporal_quality && (
                  <span className="text-[10px] font-bold bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded border border-indigo-300 uppercase">
                    {sentinelProfile.temporal_quality.replace(/_/g, ' ')}
                  </span>
                )}
              </div>

              {/* Scene Metadata */}
              <div className="space-y-1.5 text-[11px] bg-white p-2.5 rounded border border-indigo-100">
                <div className="flex justify-between border-b border-slate-100 pb-1">
                  <span className="text-slate-500">Provider & Sensor</span>
                  <span className="font-semibold text-slate-800">CDSE • Sentinel-2 L2A</span>
                </div>
                <div className="flex justify-between border-b border-slate-100 pb-1">
                  <span className="text-slate-500">Scene Identifier</span>
                  <span className="font-mono text-[10px] text-slate-700 truncate max-w-[190px]" title={sentinelProfile.scene_id || ''}>
                    {sentinelProfile.scene_id || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-100 pb-1">
                  <span className="text-slate-500">Scene Acquired (UTC)</span>
                  <span className="font-medium text-slate-800">
                    {sentinelProfile.scene_acquisition_time_utc ? new Date(sentinelProfile.scene_acquisition_time_utc).toUTCString().slice(5, 22) : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-100 pb-1">
                  <span className="text-slate-500">Catalogue Cloud Cover</span>
                  <span className="font-semibold text-slate-800">{sentinelProfile.catalogue_cloud_cover != null ? `${sentinelProfile.catalogue_cloud_cover.toFixed(1)}%` : 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Local ROI Valid Clear Pixels</span>
                  <span className="font-bold text-indigo-900">{sentinelProfile.local_valid_fraction != null ? `${(sentinelProfile.local_valid_fraction * 100).toFixed(1)}%` : 'N/A'}</span>
                </div>
              </div>

              {/* Primary Spectral Indices (250m Neighborhood Medians) */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">
                    Primary Spectral Indices (250m Medians)
                  </span>
                  <span className="text-[9px] text-slate-400">Res: 20m</span>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-white p-2 rounded border border-indigo-100 text-center">
                    <span className="text-slate-400 block text-[9px] uppercase font-bold">NDVI</span>
                    <span className="font-mono font-black text-slate-900 text-sm">
                      {sentinelProfile.stats_250m?.ndvi_median != null ? sentinelProfile.stats_250m.ndvi_median.toFixed(3) : 'N/A'}
                    </span>
                    <span className="text-[8.5px] text-slate-500 block truncate mt-0.5" title="Vegetation spectral density">
                      Vegetation
                    </span>
                  </div>

                  <div className="bg-white p-2 rounded border border-indigo-100 text-center">
                    <span className="text-slate-400 block text-[9px] uppercase font-bold">NDMI</span>
                    <span className="font-mono font-black text-slate-900 text-sm">
                      {sentinelProfile.stats_250m?.ndmi_median != null ? sentinelProfile.stats_250m.ndmi_median.toFixed(3) : 'N/A'}
                    </span>
                    <span className="text-[8.5px] text-slate-500 block truncate mt-0.5" title="Moisture / water stress">
                      Moisture
                    </span>
                  </div>

                  <div className="bg-white p-2 rounded border border-indigo-100 text-center">
                    <span className="text-slate-400 block text-[9px] uppercase font-bold">NBR</span>
                    <span className="font-mono font-black text-slate-900 text-sm">
                      {sentinelProfile.stats_250m?.nbr_median != null ? sentinelProfile.stats_250m.nbr_median.toFixed(3) : 'N/A'}
                    </span>
                    <span className="text-[8.5px] text-slate-500 block truncate mt-0.5" title="NIR-SWIR spectral context">
                      NIR-SWIR
                    </span>
                  </div>
                </div>

                {/* Point Pixel Sample */}
                <div className="bg-white/80 p-2 rounded border border-indigo-100 text-[10px] space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Point Coordinate Pixel:</span>
                    <span className="font-semibold text-slate-800">
                      {sentinelProfile.point_is_valid
                        ? `Valid (SCL: ${sentinelProfile.point_scl ?? 'N/A'})`
                        : sentinelProfile.point_scl != null
                        ? `Cloud-masked (SCL: ${sentinelProfile.point_scl})`
                        : 'Invalid / No data'}
                    </span>
                  </div>
                  {sentinelProfile.point_is_valid && (
                    <div className="grid grid-cols-3 gap-1 pt-1 border-t border-slate-100 text-center font-mono">
                      <span>NDVI: {sentinelProfile.point_ndvi != null ? sentinelProfile.point_ndvi.toFixed(3) : 'N/A'}</span>
                      <span>NDMI: {sentinelProfile.point_ndmi != null ? sentinelProfile.point_ndmi.toFixed(3) : 'N/A'}</span>
                      <span>NBR: {sentinelProfile.point_nbr != null ? sentinelProfile.point_nbr.toFixed(3) : 'N/A'}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Technical Spectral Reflectance */}
              <div className="bg-white p-2.5 rounded border border-indigo-100 text-[11px] space-y-1">
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block">
                  Surface Reflectance (250m Medians)
                </span>
                <div className="grid grid-cols-4 gap-1.5 text-center font-mono text-[10px]">
                  <div className="bg-slate-50 p-1 rounded">
                    <span className="text-slate-400 block text-[8px]">B04 (Red)</span>
                    <span className="font-bold text-slate-800">{sentinelProfile.stats_250m?.b04_median != null ? sentinelProfile.stats_250m.b04_median.toFixed(3) : 'N/A'}</span>
                  </div>
                  <div className="bg-slate-50 p-1 rounded">
                    <span className="text-slate-400 block text-[8px]">B08 (NIR)</span>
                    <span className="font-bold text-slate-800">{sentinelProfile.stats_250m?.b08_median != null ? sentinelProfile.stats_250m.b08_median.toFixed(3) : 'N/A'}</span>
                  </div>
                  <div className="bg-slate-50 p-1 rounded">
                    <span className="text-slate-400 block text-[8px]">B11 (SWIR1)</span>
                    <span className="font-bold text-slate-800">{sentinelProfile.stats_250m?.b11_median != null ? sentinelProfile.stats_250m.b11_median.toFixed(3) : 'N/A'}</span>
                  </div>
                  <div className="bg-slate-50 p-1 rounded">
                    <span className="text-slate-400 block text-[8px]">B12 (SWIR2)</span>
                    <span className="font-bold text-slate-800">{sentinelProfile.stats_250m?.b12_median != null ? sentinelProfile.stats_250m.b12_median.toFixed(3) : 'N/A'}</span>
                  </div>
                </div>
              </div>

              {/* Imagery Previews */}
              <div className="space-y-2 pt-1">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">
                    Satellite Context Preview
                  </span>
                  <div className="flex gap-1 bg-slate-100 p-0.5 rounded border border-slate-200">
                    <button
                      type="button"
                      onClick={() => setPreviewMode('true_color')}
                      className={`px-2 py-0.5 text-[9px] font-bold rounded transition-colors ${
                        previewMode === 'true_color'
                          ? 'bg-indigo-600 text-white shadow-xs'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      True Color
                    </button>
                    <button
                      type="button"
                      onClick={() => setPreviewMode('swir_context')}
                      className={`px-2 py-0.5 text-[9px] font-bold rounded transition-colors ${
                        previewMode === 'swir_context'
                          ? 'bg-indigo-600 text-white shadow-xs'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      SWIR Context
                    </button>
                  </div>
                </div>

                <div className="relative w-full aspect-square bg-slate-950 rounded-lg overflow-hidden border border-slate-800 flex items-center justify-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={apiService.getSentinelPreviewUrl(hotspot.id, previewMode)}
                    alt={`Sentinel-2 ${previewMode === 'true_color' ? 'True Color' : 'SWIR Context'}`}
                    className="w-full h-full object-cover"
                    loading="lazy"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = 'none';
                    }}
                  />
                  {/* Visual crosshair at exact center for FIRMS thermal coordinate */}
                  <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    <div className="relative">
                      <div className="w-3.5 h-3.5 rounded-full border-2 border-orange-500 bg-orange-500/30 animate-pulse"></div>
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-1 bg-white rounded-full"></div>
                    </div>
                  </div>
                  {/* Mode caption overlay */}
                  <div className="absolute bottom-1.5 left-1.5 right-1.5 bg-slate-950/80 backdrop-blur-xs text-white px-2 py-1 rounded text-[9px] flex justify-between items-center border border-white/10">
                    <span className="font-semibold text-indigo-300">
                      {previewMode === 'true_color' ? 'RGB: B04 (Red) • B03 (Green) • B02 (Blue)' : 'SWIR: B12 (SWIR2) • B11 (SWIR1) • B08 (NIR)'}
                    </span>
                    <span className="text-[8px] text-slate-400">FIRMS Point at Center</span>
                  </div>
                </div>
              </div>

              {/* Scientific Disclaimer (Section 72) */}
              <div className="pt-2 border-t border-indigo-200 text-[10px] text-slate-500 space-y-1">
                <p className="text-[9px] leading-tight text-indigo-950/80 bg-indigo-100/60 p-2 rounded border border-indigo-200/80 font-medium">
                  Notice: Sentinel-2 provides high-resolution optical/SWIR context, not direct temperature measurements. NASA FIRMS remains the authoritative thermal anomaly sensor. Cloud cover and prior acquisition timing limit interpretation.
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-200 text-xs text-slate-600 space-y-2">
              <p>
                {sentinelProfile?.provider_status === 'NO_SCENE'
                  ? 'No prior Sentinel-2 Level-2A scene found in CDSE catalog within 30-day lookback window.'
                  : sentinelProfile?.provider_status === 'PROVIDER_UNAVAILABLE'
                  ? 'CDSE provider service currently unavailable or rate-limited.'
                  : 'Sentinel-2 optical/SWIR context not evaluated yet for this observation.'}
              </p>
              {onSyncSentinel && (
                <button
                  type="button"
                  onClick={() => onSyncSentinel(hotspot.id)}
                  className="w-full mt-1.5 py-1.5 px-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded text-xs transition-colors flex items-center justify-center gap-1.5 shadow-xs"
                >
                  <Satellite size={13} />
                  Evaluate Sentinel-2 Context
                </button>
              )}
            </div>
          )}

          {/* PHASE 7 — FEATURE FUSION */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Layers size={16} className="text-violet-600" />
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Phase 7 • Feature Fusion
                </h3>
              </div>
              {fusionProfile && (
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
                    fusionProfile.fusion_status === 'COMPLETE'
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      : 'bg-amber-100 text-amber-800 border-amber-300'
                  }`}
                >
                  {fusionProfile.fusion_status}
                </span>
              )}
            </div>

            {fusionProfile ? (
              <div className="bg-violet-50/50 rounded-lg p-3.5 border border-violet-200 text-xs space-y-3">
                {/* Feature Coverage Progress Banner */}
                <div className="bg-white p-2.5 rounded border border-violet-100 space-y-1.5">
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">
                      Feature Coverage
                    </span>
                    <span className="font-black font-mono text-violet-900 text-sm">
                      {fusionProfile.feature_coverage_percent}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${
                        fusionProfile.feature_coverage_percent >= 80
                          ? 'bg-violet-600'
                          : fusionProfile.feature_coverage_percent >= 50
                          ? 'bg-amber-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${fusionProfile.feature_coverage_percent}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[9px] text-slate-400">
                    <span>
                      {fusionProfile.non_null_feature_count} / {fusionProfile.expected_feature_count} model features
                    </span>
                    <span>Schema: {fusionProfile.schema_version}</span>
                  </div>
                </div>

                {/* Evidence Groups Status */}
                <div className="space-y-1 bg-white p-2.5 rounded border border-violet-100 text-[11px]">
                  <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wider block mb-1">
                    Multi-Modal Evidence Groups
                  </span>
                  <div className="grid grid-cols-2 gap-1 text-[10px]">
                    <div className="flex items-center justify-between p-1 bg-slate-50 rounded">
                      <span className="text-slate-600">Thermal (P1)</span>
                      <span className="font-bold text-emerald-700">AVAILABLE</span>
                    </div>
                    <div className="flex items-center justify-between p-1 bg-slate-50 rounded">
                      <span className="text-slate-600">Temporal (P3)</span>
                      <span
                        className={`font-bold ${
                          fusionProfile.group_status.TEMPORAL === 'AVAILABLE'
                            ? 'text-emerald-700'
                            : fusionProfile.group_status.TEMPORAL === 'PARTIAL'
                            ? 'text-amber-600'
                            : 'text-slate-400'
                        }`}
                      >
                        {fusionProfile.group_status.TEMPORAL}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-1 bg-slate-50 rounded">
                      <span className="text-slate-600">Industry (P4)</span>
                      <span
                        className={`font-bold ${
                          fusionProfile.group_status.INDUSTRIAL === 'AVAILABLE'
                            ? 'text-emerald-700'
                            : 'text-slate-400'
                        }`}
                      >
                        {fusionProfile.group_status.INDUSTRIAL}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-1 bg-slate-50 rounded">
                      <span className="text-slate-600">Land Cover (P5)</span>
                      <span
                        className={`font-bold ${
                          fusionProfile.group_status.LAND_COVER === 'AVAILABLE'
                            ? 'text-emerald-700'
                            : fusionProfile.group_status.LAND_COVER === 'PARTIAL'
                            ? 'text-amber-600'
                            : 'text-slate-400'
                        }`}
                      >
                        {fusionProfile.group_status.LAND_COVER}
                      </span>
                    </div>
                    <div className="col-span-2 flex items-center justify-between p-1 bg-slate-50 rounded">
                      <span className="text-slate-600">Sentinel-2 (P6)</span>
                      <span
                        className={`font-bold ${
                          fusionProfile.group_status.SENTINEL === 'AVAILABLE'
                            ? 'text-emerald-700'
                            : fusionProfile.group_status.SENTINEL === 'CLOUD_LIMITED'
                            ? 'text-amber-600'
                            : 'text-slate-400'
                        }`}
                      >
                        {fusionProfile.group_status.SENTINEL.replace(/_/g, ' ')}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Compact Fused Observables Grid */}
                <div className="space-y-1 bg-white p-2.5 rounded border border-violet-100 text-[11px]">
                  <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wider block mb-1">
                    Fused Feature Highlights
                  </span>
                  <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px]">
                    <div className="flex justify-between border-b border-slate-100 pb-0.5">
                      <span className="text-slate-500">Persistence Index:</span>
                      <span className="font-mono font-bold text-slate-800">
                        {fusionProfile.feature_vector.temporal_persistence_index ?? 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-slate-100 pb-0.5">
                      <span className="text-slate-500">Active Days (30d):</span>
                      <span className="font-mono font-bold text-slate-800">
                        {fusionProfile.feature_vector.temporal_active_days_30d ?? 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-slate-100 pb-0.5">
                      <span className="text-slate-500">Industry Distance:</span>
                      <span className="font-mono font-bold text-slate-800">
                        {typeof fusionProfile.feature_vector.industrial_nearest_distance_m === 'number'
                          ? `${fusionProfile.feature_vector.industrial_nearest_distance_m.toFixed(0)}m`
                          : fusionProfile.feature_vector.industrial_coverage_status === 'UNAVAILABLE'
                          ? 'UNAVAILABLE'
                          : 'NONE (<5km)'}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-slate-100 pb-0.5">
                      <span className="text-slate-500">Inside Ind. Area:</span>
                      <span className="font-bold text-slate-800">
                        {fusionProfile.feature_vector.industrial_inside_area ? 'YES' : 'NO'}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-slate-100 pb-0.5">
                      <span className="text-slate-500">Dominant Land:</span>
                      <span className="font-bold text-slate-800 truncate max-w-[90px]">
                        {fusionProfile.feature_vector.landcover_dominant_class_500m ?? 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-slate-100 pb-0.5">
                      <span className="text-slate-500">Built-Up / Crop:</span>
                      <span className="font-mono font-bold text-slate-800">
                        {typeof fusionProfile.feature_vector.landcover_builtup_fraction_500m === 'number'
                          ? `${(fusionProfile.feature_vector.landcover_builtup_fraction_500m * 100).toFixed(0)}%`
                          : '-'}
                        {' / '}
                        {typeof fusionProfile.feature_vector.landcover_cropland_fraction_500m === 'number'
                          ? `${(fusionProfile.feature_vector.landcover_cropland_fraction_500m * 100).toFixed(0)}%`
                          : '-'}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-slate-100 pb-0.5">
                      <span className="text-slate-500">Sentinel NDVI (250m):</span>
                      <span className="font-mono font-bold text-slate-800">
                        {typeof fusionProfile.feature_vector.sentinel_ndvi_median_250m === 'number'
                          ? fusionProfile.feature_vector.sentinel_ndvi_median_250m.toFixed(3)
                          : fusionProfile.group_status.SENTINEL === 'CLOUD_LIMITED'
                          ? 'CLOUD LIMITED'
                          : 'NOT EVALUATED'}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-slate-100 pb-0.5">
                      <span className="text-slate-500">Sentinel NBR (250m):</span>
                      <span className="font-mono font-bold text-slate-800">
                        {typeof fusionProfile.feature_vector.sentinel_nbr_median_250m === 'number'
                          ? fusionProfile.feature_vector.sentinel_nbr_median_250m.toFixed(3)
                          : '-'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Fingerprint & Provenance */}
                <div className="bg-white p-2.5 rounded border border-violet-100 text-[9.5px] text-slate-400 space-y-0.5">
                  <div className="flex justify-between">
                    <span>Source Fingerprint:</span>
                    <span className="font-mono font-semibold text-slate-600 truncate max-w-[170px]" title={fusionProfile.source_fingerprint}>
                      {fusionProfile.source_fingerprint.slice(0, 16)}...
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Schema Hash:</span>
                    <span className="font-mono font-semibold text-slate-600 truncate max-w-[170px]" title={fusionProfile.schema_hash}>
                      {fusionProfile.schema_hash.slice(0, 16)}...
                    </span>
                  </div>
                </div>

                {/* Scientific Notice */}
                <div className="p-2 bg-violet-100/60 rounded border border-violet-200 text-[10px] text-violet-900 leading-tight">
                  <span className="font-bold block mb-0.5">Scientific Notice:</span>
                  Feature Fusion assembles multi-source evidence for downstream analysis. It does not itself assign fire cause, risk, or probability.
                </div>
              </div>
            ) : (
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 text-xs text-center text-slate-500">
                <Layers size={20} className="mx-auto text-slate-400 mb-1" />
                <p className="font-semibold">Feature Fusion Profile Not Synced</p>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Execute Sync Fusion in toolbar to assemble multi-source features for this observation.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Phase 8: Intelligent Classification Engine */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <BrainCircuit size={15} className="text-rose-600" />
              Classification — Phase 8
            </h3>
            {classificationProfile && (
              <span
                className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase ${
                  classificationProfile.classification_status === 'AVAILABLE'
                    ? 'bg-rose-50 text-rose-800 border-rose-200'
                    : classificationProfile.classification_status === 'INSUFFICIENT_EVIDENCE'
                    ? 'bg-amber-50 text-amber-800 border-amber-200'
                    : 'bg-slate-100 text-slate-700 border-slate-200'
                }`}
              >
                {classificationProfile.classification_status.replace(/_/g, ' ')}
              </span>
            )}
          </div>

          <div className="bg-rose-50/40 rounded-lg p-3 border border-rose-200/80 space-y-3">
            {classificationProfile ? (
              <div className="space-y-3">
                {/* Archetype Class & Score */}
                <div className="bg-white p-3 rounded-md border border-rose-100 shadow-sm">
                  <span className="text-[10px] text-rose-700 font-bold uppercase tracking-wider block mb-1">
                    Thermal Context Archetype
                  </span>
                  <p className="text-base font-black text-slate-900 leading-tight">
                    {classificationProfile.predicted_class
                      ? classificationProfile.predicted_class.replace(/_/g, ' ')
                      : 'INSUFFICIENT EVIDENCE'}
                  </p>

                  <div className="grid grid-cols-2 gap-2 mt-2.5 pt-2 border-t border-rose-50 text-xs">
                    <div>
                      <span className="text-[10.5px] text-slate-500 block">Model Score</span>
                      <span className="font-bold text-slate-900 text-sm">
                        {classificationProfile.class_score != null
                          ? `${(classificationProfile.class_score * 100).toFixed(0)}%`
                          : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10.5px] text-slate-500 block">Feature Coverage</span>
                      <span className="font-bold text-slate-900 text-sm">
                        {classificationProfile.evidence_coverage != null
                          ? `${(classificationProfile.evidence_coverage * 100).toFixed(0)}%`
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Model Metadata */}
                <div className="bg-white p-2.5 rounded-md border border-rose-100 text-xs space-y-1.5">
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-slate-500">Model:</span>
                    <span className="font-mono font-semibold text-slate-700">{classificationProfile.model_version}</span>
                  </div>
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-slate-500">Validation:</span>
                    <span className="font-bold text-rose-700 bg-rose-50 px-1.5 py-0.2 rounded border border-rose-200 text-[10px]">
                      {classificationProfile.validation_status.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>

                {/* Class Probabilities Distribution */}
                {classificationProfile.class_probabilities && (
                  <div className="bg-white p-2.5 rounded-md border border-rose-100 text-xs space-y-1.5">
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">
                      Context Probability Distribution
                    </span>
                    <div className="space-y-1">
                      {Object.entries(classificationProfile.class_probabilities).map(([cName, prob]) => (
                        <div key={cName} className="space-y-0.5">
                          <div className="flex justify-between text-[10.5px]">
                            <span className="text-slate-600 font-medium truncate max-w-[200px]">
                              {cName.replace('_THERMAL_CONTEXT', '').replace('_CONTEXT', '').replace(/_/g, ' ')}
                            </span>
                            <span className="font-mono font-bold text-slate-800">
                              {(prob * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-rose-500 rounded-full transition-all duration-300"
                              style={{ width: `${Math.max(prob * 100, 2)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Scientific Disclaimer */}
                <div className="p-2 bg-rose-100/60 rounded border border-rose-200 text-[10px] text-rose-900 leading-tight space-y-1">
                  <p>
                    <span className="font-bold">Scientific Notice:</span> Phase 8 classifies thermal-context archetypes from multi-source evidence. It does not independently confirm fire cause.
                  </p>
                  {classificationProfile.validation_status.includes('WEAK') && (
                    <p className="text-rose-800/90 italic">
                      Prototype model trained partly from conservative weak labels.
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 text-xs text-center text-slate-500">
                <BrainCircuit size={20} className="mx-auto text-slate-400 mb-1" />
                <p className="font-semibold">Classification Profile Not Synced</p>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Execute Sync Classification in dashboard to run model inference for this observation.
                </p>
              </div>
            )}
          </div>

          {/* Phase 9: Model Explainability Engine (TreeSHAP) */}
          <div className="bg-amber-50/70 rounded-lg p-4 border border-amber-200">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles size={15} className="text-amber-600" /> Model Explainability • SHAP (Phase 9)
              </span>
              {explanationProfile ? (
                <div className="flex items-center gap-1.5">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                    explanationProfile.explanation_status === 'AVAILABLE'
                      ? 'bg-emerald-100 text-emerald-900 border-emerald-300'
                      : 'bg-amber-100 text-amber-900 border-amber-300'
                  }`}>
                    {explanationProfile.explanation_status}
                  </span>
                  <span className="text-[9px] font-mono font-bold bg-amber-200/80 text-amber-950 px-1.5 py-0.5 rounded">
                    {explanationProfile.method || 'TreeSHAP'}
                  </span>
                </div>
              ) : (
                <span className="bg-slate-100 text-slate-600 border border-slate-200 text-[10px] font-semibold px-2 py-0.5 rounded">
                  Pending
                </span>
              )}
            </div>

            {explanationProfile ? (
              <div className="space-y-3">
                {/* Target Archetype & Log-Odds Margin */}
                <div className="bg-white p-3 rounded-md border border-amber-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[10px] text-amber-800 font-bold uppercase tracking-wider block">
                        Explained Target Archetype
                      </span>
                      <p className="font-black text-slate-900 text-sm mt-0.5">
                        {explanationProfile.predicted_class
                          ? explanationProfile.predicted_class.replace(/_/g, ' ')
                          : 'Unclassified / Ambiguous'}
                      </p>
                    </div>
                    {explanationProfile.prediction_score != null && (
                      <span className="text-xs font-mono font-bold bg-amber-100 text-amber-900 px-2 py-0.5 rounded border border-amber-200">
                        {(explanationProfile.prediction_score * 100).toFixed(0)}% Score
                      </span>
                    )}
                  </div>

                  {/* Additivity Verification Box */}
                  <div className="mt-2.5 pt-2 border-t border-amber-50 space-y-1.5">
                    <div className="flex items-center justify-between text-[10.5px]">
                      <span className="text-slate-500 font-medium flex items-center gap-1">
                        <Scale size={11} className="text-amber-600" />
                        Mathematical Additivity:
                      </span>
                      <span className="font-mono text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200 font-bold flex items-center gap-1">
                        <CheckCircle2 size={10} />
                        |Δ| = {Math.abs(explanationProfile.additivity_error ?? 0).toFixed(4)} (&lt; 0.01)
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[10.5px] bg-amber-50/50 p-1.5 rounded border border-amber-100/60 font-mono">
                      <div>
                        <span className="text-slate-400 block text-[9px]">Base Value (f₀)</span>
                        <span className="font-bold text-slate-700">
                          {explanationProfile.base_value != null ? explanationProfile.base_value.toFixed(3) : 'N/A'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[9px]">Model Margin f(x)</span>
                        <span className="font-bold text-slate-700">
                          {explanationProfile.explained_output != null ? explanationProfile.explained_output.toFixed(3) : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Top Supporting Features (Positive SHAP push towards class) */}
                {explanationProfile.top_supporting_features && explanationProfile.top_supporting_features.length > 0 && (
                  <div className="bg-white p-3 rounded-md border border-emerald-100 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-emerald-900 uppercase tracking-wider flex items-center gap-1 text-[10.5px]">
                        <TrendingUp size={13} className="text-emerald-600" />
                        Top Supporting Evidence (+SHAP)
                      </span>
                      <span className="text-[9.5px] text-emerald-700 font-semibold">
                        Pushes toward class
                      </span>
                    </div>

                    <div className="space-y-2 pt-1">
                      {explanationProfile.top_supporting_features.slice(0, 4).map((feat) => (
                        <div key={feat.feature_name} className="space-y-1">
                          <div className="flex justify-between items-baseline text-[10.5px]">
                            <div className="min-w-0 max-w-[210px]">
                              <span className="font-bold text-slate-800 truncate block" title={feat.display_name}>
                                {feat.display_name}
                              </span>
                              <span className="text-[9.5px] text-slate-500 block">
                                Value: <span className="font-medium text-slate-700">{feat.display_value}</span> {feat.unit}
                              </span>
                            </div>
                            <span className="font-mono font-bold text-emerald-600 text-xs shrink-0">
                              +{feat.contribution.toFixed(3)}
                            </span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                              style={{ width: `${Math.max(feat.relative_strength * 100, 4)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Top Opposing Features (Negative SHAP push away from class) */}
                {explanationProfile.top_opposing_features && explanationProfile.top_opposing_features.length > 0 && (
                  <div className="bg-white p-3 rounded-md border border-rose-100 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-rose-900 uppercase tracking-wider flex items-center gap-1 text-[10.5px]">
                        <TrendingDown size={13} className="text-rose-600" />
                        Top Opposing Evidence (-SHAP)
                      </span>
                      <span className="text-[9.5px] text-rose-700 font-semibold">
                        Pushes away from class
                      </span>
                    </div>

                    <div className="space-y-2 pt-1">
                      {explanationProfile.top_opposing_features.slice(0, 3).map((feat) => (
                        <div key={feat.feature_name} className="space-y-1">
                          <div className="flex justify-between items-baseline text-[10.5px]">
                            <div className="min-w-0 max-w-[210px]">
                              <span className="font-bold text-slate-800 truncate block" title={feat.display_name}>
                                {feat.display_name}
                              </span>
                              <span className="text-[9.5px] text-slate-500 block">
                                Value: <span className="font-medium text-slate-700">{feat.display_value}</span> {feat.unit}
                              </span>
                            </div>
                            <span className="font-mono font-bold text-rose-600 text-xs shrink-0">
                              {feat.contribution.toFixed(3)}
                            </span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-rose-500 rounded-full transition-all duration-300"
                              style={{ width: `${Math.max(feat.relative_strength * 100, 4)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Domain Group Contributions Breakdown */}
                {explanationProfile.group_contributions && Object.keys(explanationProfile.group_contributions).length > 0 && (
                  <div className="bg-white p-3 rounded-md border border-amber-100 space-y-2">
                    <span className="text-[10px] text-amber-800 font-bold uppercase tracking-wider block">
                      Domain Group Contribution Breakdown
                    </span>
                    <div className="space-y-1.5">
                      {Object.entries(explanationProfile.group_contributions).map(([grp, item]) => {
                        const isSupp = item.direction === 'SUPPORTS';
                        return (
                          <div key={grp} className="space-y-0.5">
                            <div className="flex justify-between text-[10.5px]">
                              <span className="text-slate-700 font-semibold">
                                {grp.replace('_', ' ')} ({item.feature_count} features)
                              </span>
                              <span className={`font-mono font-bold ${isSupp ? 'text-emerald-600' : 'text-rose-600'}`}>
                                {isSupp ? '+' : ''}{item.total_contribution.toFixed(3)}
                              </span>
                            </div>
                            <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-300 ${
                                  isSupp ? 'bg-emerald-500' : 'bg-rose-500'
                                }`}
                                style={{ width: `${Math.max(item.relative_strength * 100, 3)}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Quality Flags & Model Metadata */}
                <div className="bg-white p-2.5 rounded-md border border-amber-100 text-xs space-y-1.5">
                  <div className="flex justify-between items-center text-[10.5px]">
                    <span className="text-slate-500">Explainer Model:</span>
                    <span className="font-mono font-semibold text-slate-700">{explanationProfile.model_version}</span>
                  </div>
                  {explanationProfile.quality_flags && explanationProfile.quality_flags.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {explanationProfile.quality_flags.map((flag) => (
                        <span key={flag} className="text-[9px] font-mono bg-amber-50 text-amber-800 px-1.5 py-0.2 rounded border border-amber-200">
                          {flag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Scientific Notice */}
                <div className="p-2 bg-amber-100/60 rounded border border-amber-200 text-[10px] text-amber-900 leading-tight space-y-1">
                  <p>
                    <span className="font-bold">Scientific Notice:</span> Phase 9 TreeSHAP local attributions decompose the log-odds margin of the frozen classifier into additive feature components. It explains archetype attribution without modifying model weights.
                  </p>
                </div>
              </div>
            ) : (
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 text-xs text-center text-slate-500 space-y-2">
                <Sparkles size={20} className="mx-auto text-amber-500 mb-1" />
                <p className="font-semibold text-slate-700">SHAP Explanation Not Synced</p>
                <p className="text-[10px] text-slate-400">
                  Execute Sync SHAP in dashboard to compute local TreeSHAP attributions for this observation.
                </p>
                {onSyncExplanation && hotspot?.id && (
                  <button
                    onClick={() => onSyncExplanation(hotspot.id)}
                    className="mt-1 px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded text-[10.5px] font-bold transition-colors inline-flex items-center gap-1"
                  >
                    <Sparkles size={12} />
                    Compute Observation SHAP
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
