"use client";

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { api, Hotspot, AnalysisResponse } from '../services/api';
import { StatsCards } from './StatsCards';
import { AnalysisDrawer } from './AnalysisDrawer';
import { Activity } from 'lucide-react';

// Dynamically import Map without SSR
const Map = dynamic(() => import('./Map'), { ssr: false });

export function Dashboard() {
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  useEffect(() => {
    async function loadHotspots() {
      try {
        const data = await api.getHotspots();
        setHotspots(data.hotspots);
      } catch (error) {
        console.error("Failed to load hotspots:", error);
      }
    }
    loadHotspots();
  }, []);

  const handleHotspotClick = async (hotspot: Hotspot) => {
    setSelectedHotspot(hotspot);
    setAnalysis(null);
    setLoadingAnalysis(true);
    try {
      const result = await api.analyzeHotspot(hotspot.latitude, hotspot.longitude);
      setAnalysis(result);
    } catch (error) {
      console.error("Failed to analyze hotspot:", error);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const handleCloseDrawer = () => {
    setSelectedHotspot(null);
    setAnalysis(null);
  };

  return (
    <div className="flex flex-col h-screen w-full bg-gray-100 overflow-hidden">
      {/* Navbar */}
      <header className="bg-slate-900 text-white p-4 flex items-center justify-between z-20 shadow-md">
        <div className="flex items-center gap-2">
          <Activity size={24} className="text-orange-500" />
          <h1 className="text-xl font-bold tracking-wider">AGNIDRISHTI AI</h1>
        </div>
        <div className="text-sm font-medium text-slate-400">
          SIH26162 - Intelligence Dashboard (Phase 0)
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 relative flex flex-col">
        {/* Top Stats Overlay */}
        <div className="absolute top-0 left-0 w-full z-10 pointer-events-none p-4">
          <div className="pointer-events-auto">
            <StatsCards total={hotspots.length} />
          </div>
        </div>

        {/* Filters Panel (Mocked UI) */}
        <div className="absolute left-4 top-40 z-10 bg-white p-3 rounded-lg shadow-lg pointer-events-auto border border-gray-200">
          <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Filters</h3>
          <div className="flex flex-col gap-2">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="radio" name="filter" defaultChecked className="accent-blue-600" /> All
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="radio" name="filter" className="accent-blue-600" /> Industrial
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="radio" name="filter" className="accent-blue-600" /> Persistent
            </label>
          </div>
        </div>

        {/* Map Container */}
        <div className="flex-1 w-full relative z-0">
          <Map hotspots={hotspots} onHotspotClick={handleHotspotClick} />
        </div>

        {/* Analysis Drawer */}
        <AnalysisDrawer 
          hotspot={selectedHotspot} 
          analysis={analysis} 
          loading={loadingAnalysis}
          onClose={handleCloseDrawer}
        />
      </div>
    </div>
  );
}
