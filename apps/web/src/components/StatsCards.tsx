import { Flame, AlertTriangle, Factory, ShieldAlert } from 'lucide-react';

interface StatsCardsProps {
  total: number;
  industrial?: number;
  persistent?: number;
  highRisk?: number;
  isLive?: boolean;
  noaa20?: number;
  noaa21?: number;
}

export function StatsCards({
  total,
  industrial = 0,
  persistent = 0,
  highRisk = 0,
  isLive = true,
  noaa20 = 0,
  noaa21 = 0,
}: StatsCardsProps) {
  if (isLive) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 z-10 w-full">
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200 flex items-center gap-4">
          <div className="p-3 bg-red-100 text-red-600 rounded-full">
            <Flame size={24} />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Active Detections</p>
            <p className="text-2xl font-black text-gray-900">{total}</p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow border border-gray-200 flex items-center gap-4">
          <div className="p-3 bg-purple-100 text-purple-600 rounded-full">
            <ShieldAlert size={24} />
          </div>
          <div>
            <p className="text-xs text-purple-700 font-semibold uppercase tracking-wider">Phase 3 • Persistent</p>
            <p className="text-2xl font-black text-purple-950">{persistent}</p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow border border-gray-200 flex items-center gap-4">
          <div className="p-3 bg-cyan-100 text-cyan-700 rounded-full">
            <Factory size={24} />
          </div>
          <div>
            <p className="text-xs text-cyan-800 font-semibold uppercase tracking-wider">Phase 4 • Mapped Industry</p>
            <p className="text-2xl font-black text-cyan-950">{industrial}</p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow border border-gray-200 flex items-center gap-4">
          <div className="p-3 bg-orange-100 text-orange-600 rounded-full">
            <AlertTriangle size={24} />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Sensors (N20 / N21)</p>
            <p className="text-2xl font-black text-gray-900">{noaa20} <span className="text-base font-normal text-gray-400">/</span> {noaa21}</p>
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
