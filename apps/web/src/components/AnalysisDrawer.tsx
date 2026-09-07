import { X, CheckCircle, AlertTriangle, Info } from 'lucide-react';
import { AnalysisResponse, Hotspot } from '../services/api';

interface AnalysisDrawerProps {
  hotspot: Hotspot | null;
  analysis: AnalysisResponse | null;
  loading: boolean;
  onClose: () => void;
}

export function AnalysisDrawer({ hotspot, analysis, loading, onClose }: AnalysisDrawerProps) {
  if (!hotspot) return null;

  return (
    <div className="absolute top-0 right-0 h-full w-96 bg-white shadow-2xl z-[1000] flex flex-col transform transition-transform duration-300 ease-in-out border-l border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-800">AGNIDRISHTI ANALYSIS</h2>
        <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded-full transition-colors">
          <X size={20} className="text-gray-500" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {loading ? (
          <div className="flex justify-center items-center h-full">
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
        )}
      </div>
    </div>
  );
}
