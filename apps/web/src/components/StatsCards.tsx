import { Flame, AlertTriangle, Factory, ShieldAlert } from 'lucide-react';

interface StatsCardsProps {
  total: number;
  industrial: number;
  persistent: number;
  highRisk: number;
}

export function StatsCards({ total, industrial, persistent, highRisk }: StatsCardsProps) {
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
          <p className="text-sm text-gray-500 font-medium">Persistent Sources</p>
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
