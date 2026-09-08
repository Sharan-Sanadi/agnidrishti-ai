import { X, CheckCircle, AlertTriangle, Info, Satellite, Flame, Clock, Compass, Hash, ShieldCheck, Database, History } from 'lucide-react';
import { AnalysisResponse, Hotspot, PersistenceProfileResponse } from '../services/api';

interface AnalysisDrawerProps {
  hotspot: Hotspot | null;
  analysis: AnalysisResponse | null;
  persistenceProfile?: PersistenceProfileResponse | null;
  loading: boolean;
  onClose: () => void;
}

export function AnalysisDrawer({ hotspot, analysis, persistenceProfile, loading, onClose }: AnalysisDrawerProps) {
  if (!hotspot) return null;

  const isLive = Boolean(hotspot.is_live_firms);

  const conf = (hotspot.confidence || '').toLowerCase();
  const confLabel = conf === 'h' ? 'High' : conf === 'n' ? 'Nominal' : conf === 'l' ? 'Low' : hotspot.confidence;
  const dayNightLabel = hotspot.day_night === 'D' ? 'Day (D)' : hotspot.day_night === 'N' ? 'Night (N)' : (hotspot.day_night || 'N/A');

  return (
    <div className="absolute top-0 right-0 h-full w-96 bg-white shadow-2xl z-[1000] flex flex-col transform transition-transform duration-300 ease-in-out border-l border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-slate-900 text-white">
        <div className="flex items-center gap-2">
          <Satellite size={20} className="text-orange-400" />
          <h2 className="text-sm font-bold tracking-wide uppercase">
            {isLive ? 'NASA FIRMS Observation' : 'Agnidrishti Mock Analysis'}
          </h2>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded-full transition-colors text-slate-300">
          <X size={18} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {isLive ? (
          /* Real Phase 1 NASA FIRMS Satellite Metadata */
          <>
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
                {hotspot.frp_mw != null ? `${hotspot.frp_mw} MW` : 'FRP Available'}
              </p>
              <p className="text-xs text-slate-600 mt-1">
                Fire Radiative Power (MW) measured by VIIRS sensor
              </p>

              <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-orange-200/80 text-xs">
                <div>
                  <span className="text-slate-500 font-medium block">Brightness (TI4)</span>
                  <span className="font-bold text-slate-900 text-sm">
                    {hotspot.brightness_ti4 != null ? `${hotspot.brightness_ti4} K` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 font-medium block">Brightness (TI5)</span>
                  <span className="font-bold text-slate-900 text-sm">
                    {hotspot.brightness_ti5 != null ? `${hotspot.brightness_ti5} K` : 'N/A'}
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
                      {new Date(hotspot.acquired_at).toISOString()}
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
            {persistenceProfile ? (
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
                    <div>
                      <span className="text-slate-500 block text-[11px]">Raw Detections (30d)</span>
                      <span className="font-bold text-slate-900 text-sm">{persistenceProfile.raw_detection_count_30d}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[11px]">Active Weeks (30d)</span>
                      <span className="font-bold text-slate-900 text-sm">{persistenceProfile.active_weeks_30d} weeks</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[11px]">Temporal Span</span>
                      <span className="font-bold text-slate-900 text-sm">{persistenceProfile.temporal_span_days_30d.toFixed(1)} days</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[11px]">Dataset Coverage</span>
                      <span className="font-bold text-slate-900 text-sm">{persistenceProfile.history_coverage_days_30d} / 30 days</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-purple-200/80 text-[11px] text-purple-900 leading-relaxed bg-white/60 p-2.5 rounded border border-purple-100">
                    <p className="font-medium">{persistenceProfile.explanation}</p>
                    <p className="mt-1 text-[10px] text-slate-500">
                      Association Radius: {persistenceProfile.radius_m}m | Algorithm: {persistenceProfile.algorithm_version}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-200 text-xs text-slate-700 leading-relaxed">
                <div className="flex items-center gap-1.5 font-bold mb-1 text-slate-900">
                  <ShieldCheck size={16} className="text-emerald-600" /> Phase 3 Temporal Intelligence Active
                </div>
                <p>
                  PostGIS spatiotemporal analysis engine active on 750m spatial radius with 30-day lookback.
                </p>
              </div>
            )}
          </>
        ) : (
          /* Phase 0 Fixture Mode Analysis */
          loading ? (
            <div className="flex justify-center items-center h-48">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : analysis ? (
            <>
              {/* Classification Card */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Classification</span>
                  <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded">
                    {Math.round(analysis.classification.confidence * 100)}% Conf
                  </span>
                </div>
                <p className="text-xl font-bold text-gray-900">{analysis.classification.subclass.replace(/_/g, ' ')}</p>

                <div className="mt-4 flex items-center justify-between border-t border-gray-200 pt-3">
                  <span className="text-sm font-medium text-gray-600">AgniRisk Score</span>
                  <span className="text-lg font-bold text-red-600">{Math.round(analysis.anomaly_score * 100)} / 100</span>
                </div>
              </div>

              {/* Why Panel */}
              <div>
                <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wider mb-3">Why this classification?</h3>
                <div className="space-y-2">
                  {analysis.classification.evidence.map((item, idx) => (
                    <div key={idx} className="flex gap-3 text-sm text-gray-700 bg-white p-2 rounded border border-gray-100">
                      <CheckCircle size={16} className="text-green-500 flex-shrink-0 mt-0.5" />
                      <span>{item.label}: <span className="font-semibold">{item.value} {item.unit || ''}</span></span>
                    </div>
                  ))}
                  <div className="flex gap-3 text-sm text-gray-700 bg-white p-2 rounded border border-gray-100">
                    <Info size={16} className="text-blue-500 flex-shrink-0 mt-0.5" />
                    <span>Land cover: <span className="font-semibold">{analysis.landcover_context?.dominant_class?.replace(/_/g, ' ') || 'Unknown'}</span></span>
                  </div>
                </div>
              </div>

              {/* Reasoning Summary */}
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                <p className="text-sm text-blue-900 leading-relaxed">
                  {analysis.classification.reasoning_summary}
                </p>
              </div>

              {/* Metadata Footer */}
              <div className="border-t border-gray-200 pt-4 text-xs text-gray-500 space-y-1">
                <p>Nearest source: {analysis.industrial_context?.distance_to_nearest_m ? `${analysis.industrial_context.distance_to_nearest_m}m` : 'Unknown'}</p>
                <p>Satellite: {hotspot.source} | FRP: {hotspot.frp_mw} MW</p>
                {analysis.warnings.map((w, idx) => (
                  <p key={idx} className="text-red-500 flex items-center gap-1 mt-2">
                    <AlertTriangle size={12} /> {w}
                  </p>
                ))}
              </div>
            </>
          ) : (
            <div className="text-center text-gray-500 mt-10">
              Failed to load analysis.
            </div>
          )
        )}
      </div>
    </div>
  );
}
