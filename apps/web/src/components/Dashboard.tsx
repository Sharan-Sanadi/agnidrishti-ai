"use client";

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { api, Hotspot, AnalysisResponse, FIRMSHotspotsResponse } from '../services/api';
import { StatsCards } from './StatsCards';
import { AnalysisDrawer } from './AnalysisDrawer';
import { Activity, RefreshCw, Satellite, AlertCircle, Database } from 'lucide-react';

// Dynamically import Map without SSR
const Map = dynamic(() => import('./Map'), { ssr: false });

type DataMode = 'live' | 'fixture';
type LiveFilter = 'all' | 'noaa20' | 'noaa21' | 'day' | 'night';
type FixtureFilter = 'all' | 'industrial' | 'persistent';

export function Dashboard() {
  const [dataMode, setDataMode] = useState<DataMode>('live');
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Live FIRMS Metadata
  const [firmsMeta, setFirmsMeta] = useState<FIRMSHotspotsResponse | null>(null);
  const [liveFilter, setLiveFilter] = useState<LiveFilter>('all');
  const [dayRange, setDayRange] = useState<number>(1);

  // Phase 0 Fixture Filter
  const [fixtureFilter, setFixtureFilter] = useState<FixtureFilter>('all');

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    let isMounted = true;

    async function fetchData() {
      try {
        if (dataMode === 'live') {
          const response = await api.getFIRMSHotspots({
            days: dayRange,
            force_refresh: refreshTrigger > 0,
          });
          if (!isMounted) return;

          setFirmsMeta(response);
          const mapped: Hotspot[] = response.observations.map((obs) => ({
            id: obs.id,
            latitude: obs.latitude,
            longitude: obs.longitude,
            acquired_at: obs.acquisition_time_utc,
            source: obs.source,
            satellite: obs.satellite,
            instrument: obs.instrument,
            frp_mw: obs.frp,
            brightness_ti4: obs.bright_ti4,
            brightness_ti5: obs.bright_ti5,
            confidence: obs.confidence,
            day_night: obs.daynight,
            scan: obs.scan,
            track: obs.track,
            firms_version: obs.firms_version,
            ingestion_time_utc: obs.ingestion_time_utc,
            is_live_firms: true,
          }));
          setHotspots(mapped);
          setErrorMessage(null);
        } else {
          const data = await api.getHotspots();
          if (!isMounted) return;
          setHotspots(data.hotspots);
          setFirmsMeta(null);
          setErrorMessage(null);
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        console.error("Failed to load hotspot data:", err);
        let msg = "Failed to communicate with the Agnidrishti API backend.";
        if (typeof err === "object" && err !== null && "response" in err) {
          const axiosErr = err as { response?: { data?: { detail?: { code?: string; message?: string } | string } } };
          const detail = axiosErr.response?.data?.detail;
          if (typeof detail === "object" && detail?.message) {
            msg = `[${detail.code || "ERROR"}] ${detail.message}`;
          } else if (typeof detail === "string") {
            msg = detail;
          }
        }
        setErrorMessage(msg);
        setHotspots([]);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [dataMode, dayRange, refreshTrigger]);

  const handleManualRefresh = () => {
    setLoading(true);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleHotspotClick = async (hotspot: Hotspot) => {
    setSelectedHotspot(hotspot);
    setAnalysis(null);

    // Only run mock analysis for Phase 0 fixtures
    if (!hotspot.is_live_firms) {
      setLoadingAnalysis(true);
      try {
        const result = await api.analyzeHotspot(hotspot.latitude, hotspot.longitude);
        setAnalysis(result);
      } catch (error) {
        console.error("Failed to analyze hotspot:", error);
      } finally {
        setLoadingAnalysis(false);
      }
    }
  };

  const handleCloseDrawer = () => {
    setSelectedHotspot(null);
    setAnalysis(null);
  };

  // Filtered hotspots
  const filteredHotspots = hotspots.filter((h) => {
    if (dataMode === 'live') {
      if (liveFilter === 'noaa20') return (h.source || '').includes('NOAA20') || h.satellite === 'N20';
      if (liveFilter === 'noaa21') return (h.source || '').includes('NOAA21') || h.satellite === 'N21';
      if (liveFilter === 'day') return h.day_night === 'D';
      if (liveFilter === 'night') return h.day_night === 'N';
      return true;
    } else {
      if (fixtureFilter === 'industrial') return h.classification === 'industrial';
      if (fixtureFilter === 'persistent') return h.persistent;
      return true;
    }
  });

  // Calculate live counts
  const noaa20Count = hotspots.filter(h => (h.source || '').includes('NOAA20') || h.satellite === 'N20').length;
  const noaa21Count = hotspots.filter(h => (h.source || '').includes('NOAA21') || h.satellite === 'N21').length;

  return (
    <div className="flex flex-col h-screen w-full bg-gray-100 overflow-hidden font-sans">
      {/* Header Bar */}
      <header className="bg-slate-950 text-white px-5 py-3.5 flex items-center justify-between z-20 shadow-lg border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-orange-500/20 rounded-lg border border-orange-500/30">
            <Activity size={22} className="text-orange-500" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-lg font-black tracking-wider text-white">AGNIDRISHTI AI</h1>
              <span className="text-[10px] font-bold tracking-widest uppercase bg-slate-800 border border-slate-700 text-slate-300 px-2 py-0.5 rounded">
                SIH26162
              </span>
            </div>
            <p className="text-xs font-medium text-slate-400">
              {dataMode === 'live' ? (
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  NASA FIRMS — Live Satellite Ingestion Pipeline (VIIRS NOAA-20 & NOAA-21)
                </span>
              ) : (
                <span className="text-amber-400">Phase 0 Local Fixture Mode (Offline Development)</span>
              )}
            </p>
          </div>
        </div>

        {/* Header Controls */}
        <div className="flex items-center gap-3">
          {/* Mode Switcher */}
          <div className="bg-slate-900 border border-slate-800 p-1 rounded-lg flex items-center gap-1 text-xs">
            <button
              onClick={() => setDataMode('live')}
              className={`px-3 py-1 rounded font-semibold transition-all flex items-center gap-1.5 ${
                dataMode === 'live'
                  ? 'bg-orange-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Satellite size={14} /> LIVE (NASA FIRMS)
            </button>
            <button
              onClick={() => setDataMode('fixture')}
              className={`px-3 py-1 rounded font-semibold transition-all flex items-center gap-1.5 ${
                dataMode === 'fixture'
                  ? 'bg-slate-700 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Database size={14} /> Fixture Mode
            </button>
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleManualRefresh}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
            title="Refresh satellite data from API"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin text-orange-400' : ''} />
            <span>{loading ? 'Ingesting...' : 'Refresh'}</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 relative flex flex-col">
        {/* Top Stats Overlay */}
        <div className="absolute top-0 left-0 w-full z-10 pointer-events-none p-4">
          <div className="pointer-events-auto">
            <StatsCards
              total={filteredHotspots.length}
              isLive={dataMode === 'live'}
              noaa20={noaa20Count}
              noaa21={noaa21Count}
              industrial={hotspots.filter(h => h.classification === 'industrial').length}
              persistent={hotspots.filter(h => h.persistent).length}
              highRisk={hotspots.filter(h => h.risk === 'high').length}
            />
          </div>
        </div>

        {/* Error Banner */}
        {errorMessage && (
          <div className="absolute top-28 left-4 right-4 z-20 pointer-events-auto bg-red-50 border border-red-300 text-red-800 px-4 py-3 rounded-lg shadow-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle size={18} className="text-red-600 shrink-0" />
              <span className="text-xs font-semibold">{errorMessage}</span>
            </div>
            <button
              onClick={handleManualRefresh}
              className="text-xs font-bold underline hover:text-red-950 ml-4"
            >
              Retry
            </button>
          </div>
        )}

        {/* Filters Panel */}
        <div className="absolute left-4 top-36 z-10 bg-white/95 backdrop-blur-sm p-3.5 rounded-xl shadow-xl pointer-events-auto border border-gray-200/80 w-56 text-xs">
          <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-gray-100">
            <h3 className="font-bold text-gray-700 uppercase tracking-wider">
              {dataMode === 'live' ? 'Satellite Filters' : 'Phase 0 Filters'}
            </h3>
            {dataMode === 'live' && (
              <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-1.5 py-0.5 rounded">
                Live
              </span>
            )}
          </div>

          {dataMode === 'live' ? (
            <div className="space-y-3">
              <div className="flex flex-col gap-1.5">
                <label className="flex items-center gap-2 cursor-pointer font-medium text-gray-700 hover:text-gray-900">
                  <input
                    type="radio"
                    name="live_filter"
                    checked={liveFilter === 'all'}
                    onChange={() => setLiveFilter('all')}
                    className="accent-orange-600"
                  />
                  All Sensors ({hotspots.length})
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-gray-700 hover:text-gray-900">
                  <input
                    type="radio"
                    name="live_filter"
                    checked={liveFilter === 'noaa20'}
                    onChange={() => setLiveFilter('noaa20')}
                    className="accent-orange-600"
                  />
                  VIIRS NOAA-20 ({noaa20Count})
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-gray-700 hover:text-gray-900">
                  <input
                    type="radio"
                    name="live_filter"
                    checked={liveFilter === 'noaa21'}
                    onChange={() => setLiveFilter('noaa21')}
                    className="accent-orange-600"
                  />
                  VIIRS NOAA-21 ({noaa21Count})
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-gray-700 hover:text-gray-900">
                  <input
                    type="radio"
                    name="live_filter"
                    checked={liveFilter === 'day'}
                    onChange={() => setLiveFilter('day')}
                    className="accent-orange-600"
                  />
                  Daytime (D)
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-gray-700 hover:text-gray-900">
                  <input
                    type="radio"
                    name="live_filter"
                    checked={liveFilter === 'night'}
                    onChange={() => setLiveFilter('night')}
                    className="accent-orange-600"
                  />
                  Nighttime (N)
                </label>
              </div>

              {/* Day Range Selector */}
              <div className="pt-2.5 border-t border-gray-100">
                <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block mb-1">
                  NASA Day Range
                </span>
                <div className="grid grid-cols-3 gap-1">
                  {[1, 2, 3].map((d) => (
                    <button
                      key={d}
                      onClick={() => setDayRange(d)}
                      className={`py-1 rounded text-center font-bold transition-all ${
                        dayRange === d
                          ? 'bg-slate-900 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {d} {d === 1 ? 'Day' : 'Days'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Provenance Footer */}
              {firmsMeta && (
                <div className="pt-2 border-t border-gray-100 text-[10px] text-gray-500 space-y-0.5">
                  <p><strong>Provider:</strong> NASA FIRMS</p>
                  <p><strong>Status:</strong> {firmsMeta.data_status.toUpperCase()}</p>
                  <p><strong>Fetched:</strong> {new Date(firmsMeta.fetched_at).toLocaleTimeString()}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="fixture_filter"
                  checked={fixtureFilter === 'all'}
                  onChange={() => setFixtureFilter('all')}
                  className="accent-blue-600"
                />
                All Detections
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="fixture_filter"
                  checked={fixtureFilter === 'industrial'}
                  onChange={() => setFixtureFilter('industrial')}
                  className="accent-blue-600"
                />
                Industrial
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="fixture_filter"
                  checked={fixtureFilter === 'persistent'}
                  onChange={() => setFixtureFilter('persistent')}
                  className="accent-blue-600"
                />
                Persistent
              </label>
            </div>
          )}
        </div>

        {/* Map Container */}
        <div className="flex-1 w-full relative z-0">
          <Map hotspots={filteredHotspots} onHotspotClick={handleHotspotClick} />
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
