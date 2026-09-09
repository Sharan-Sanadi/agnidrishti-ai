import { Flame, AlertTriangle, Factory, ShieldAlert, Trees } from 'lucide-react';

interface StatsCardsProps {
  total: number;
  industrial?: number;
  persistent?: number;
  landCoverEvaluated?: number;
  highRisk?: number;
  isLive?: boolean;
  noaa20?: number;
  noaa21?: number;
}

export function StatsCards({
  total,
  industrial = 0,
  persistent = 0,
  landCoverEvaluated = 0,
  highRisk = 0,
  isLive = true,
  noaa20 = 0,
  noaa21 = 0,
}: StatsCardsProps) {
  if (isLive) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 p-4 z-10 w-full">
        <div className="bg-white p-3.5 rounded-lg shadow border border-gray-200 flex items-center gap-3.5">
          <div className="p-2.5 bg-red-100 text-red-600 rounded-full shrink-0">
            <Flame size={22} />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] text-gray-500 font-semibold uppercase tracking-wider truncate">Active Detections</p>
            <p className="text-xl font-black text-gray-900">{total}</p>
          </div>
        </div>

        <div className="bg-white p-3.5 rounded-lg shadow border border-gray-200 flex items-center gap-3.5">
          <div className="p-2.5 bg-purple-100 text-purple-600 rounded-full shrink-0">
            <ShieldAlert size={22} />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] text-purple-700 font-semibold uppercase tracking-wider truncate">Phase 3 • Persistent</p>
            <p className="text-xl font-black text-purple-950">{persistent}</p>
          </div>
        </div>

        <div className="bg-white p-3.5 rounded-lg shadow border border-gray-200 flex items-center gap-3.5">
          <div className="p-2.5 bg-cyan-100 text-cyan-700 rounded-full shrink-0">
            <Factory size={22} />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] text-cyan-800 font-semibold uppercase tracking-wider truncate">Phase 4 • Industry</p>
            <p className="text-xl font-black text-cyan-950">{industrial}</p>
          </div>
        </div>

        <div className="bg-white p-3.5 rounded-lg shadow border border-gray-200 flex items-center gap-3.5">
          <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-full shrink-0">
            <Trees size={22} />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] text-emerald-800 font-semibold uppercase tracking-wider truncate">Phase 5 • Land Cover</p>
            <p className="text-xl font-black text-emerald-950">{landCoverEvaluated}</p>
          </div>
        </div>

        <div className="bg-white p-3.5 rounded-lg shadow border border-gray-200 flex items-center gap-3.5">
          <div className="p-2.5 bg-orange-100 text-orange-600 rounded-full shrink-0">
            <AlertTriangle size={22} />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] text-gray-500 font-semibold uppercase tracking-wider truncate">Sensors (N20 / N21)</p>
            <p className="text-xl font-black text-gray-900">{noaa20} <span className="text-sm font-normal text-gray-400">/</span> {noaa21}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 z-10 w-full">
      <div className="bg-white p-4 rounded-lg shadow border border-gray-200 flex items-center gap-4">
        <div className="p-3 bg-red-100 text-red-600 rounded-full">
          <Flame size={24} />
        </div>
        <div>
          <p className="text-sm text-gray-500 font-medium">Active Hotspots</p>
          <p className="text-2xl font-bold text-gray-900">{total}</p>
        </div>
      </div>
      
      <div className="bg-white p-4 rounded-lg shadow border border-gray-200 flex items-center gap-4">
        <div className="p-3 bg-orange-100 text-orange-600 rounded-full">
          <Factory size={24} />
        </div>
        <div>
          <p className="text-sm text-gray-500 font-medium">Probable Industrial</p>
          <p className="text-2xl font-bold text-gray-900">{industrial}</p>
        </div>
      </div>

      <div className="bg-white p-4 rounded-lg shadow border border-gray-200 flex items-center gap-4">
        <div className="p-3 bg-blue-100 text-blue-600 rounded-full">
          <AlertTriangle size={24} />
        </div>
        <div>
          <p className="text-sm text-gray-500 font-medium">Persistent Thermal</p>
          <p className="text-2xl font-bold text-gray-900">{persistent}</p>
        </div>
      </div>

      <div className="bg-white p-4 rounded-lg shadow border border-gray-200 flex items-center gap-4">
        <div className="p-3 bg-purple-100 text-purple-600 rounded-full">
          <ShieldAlert size={24} />
        </div>
        <div>
          <p className="text-sm text-gray-500 font-medium">High Risk</p>
          <p className="text-2xl font-bold text-gray-900">{highRisk}</p>
        </div>
      </div>
    </div>
  );
}
