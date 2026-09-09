import { Flame, AlertTriangle, Factory, ShieldAlert, Trees, Satellite, Layers, BrainCircuit } from 'lucide-react';

interface StatsCardsProps {
  total: number;
  industrial?: number;
  persistent?: number;
  landCoverEvaluated?: number;
  sentinelEvaluated?: number;
  sentinelClear?: number;
  fusionComplete?: number;
  fusionPartial?: number;
  classificationCount?: number;
  classificationIndustrial?: number;
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
  sentinelEvaluated = 0,
  sentinelClear = 0,
  fusionComplete = 0,
  fusionPartial = 0,
  classificationCount = 0,
  classificationIndustrial = 0,
  highRisk = 0,
  isLive = true,
  noaa20 = 0,
  noaa21 = 0,
}: StatsCardsProps) {
  if (isLive) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-8 gap-3 p-4 z-10 w-full">
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
          <div className="p-2.5 bg-indigo-100 text-indigo-700 rounded-full shrink-0">
            <Satellite size={22} />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] text-indigo-800 font-semibold uppercase tracking-wider truncate">Phase 6 • Sentinel-2</p>
            <div className="flex items-baseline gap-1.5">
              <p className="text-xl font-black text-indigo-950">{sentinelEvaluated}</p>
              {sentinelClear > 0 && (
                <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">
                  {sentinelClear} CLR
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white p-3.5 rounded-lg shadow border border-gray-200 flex items-center gap-3.5">
          <div className="p-2.5 bg-violet-100 text-violet-700 rounded-full shrink-0">
            <Layers size={22} />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] text-violet-800 font-semibold uppercase tracking-wider truncate">Phase 7 • Fusion</p>
            <div className="flex items-baseline gap-1.5">
              <p className="text-xl font-black text-violet-950">{fusionComplete}</p>
              {fusionPartial > 0 && (
                <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                  {fusionPartial} PART
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white p-3.5 rounded-lg shadow border border-gray-200 flex items-center gap-3.5">
          <div className="p-2.5 bg-rose-100 text-rose-700 rounded-full shrink-0">
            <BrainCircuit size={22} />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] text-rose-800 font-semibold uppercase tracking-wider truncate">Phase 8 • Classified</p>
            <div className="flex items-baseline gap-1.5">
              <p className="text-xl font-black text-rose-950">{classificationCount}</p>
              {classificationIndustrial > 0 && (
                <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                  {classificationIndustrial} IND
                </span>
              )}
            </div>
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
