"use client";

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import {
  apiService,
  ThermalObservation,
  AnalysisResponse,
  FIRMSHotspotsResponse,
  PersistenceProfileResponse,
  IndustrialContextProfileResponse,
  OSMFeatureCollection,
} from '../services/api';
import { StatsCards } from './StatsCards';
import { AnalysisDrawer } from './AnalysisDrawer';
import { Activity, RefreshCw, AlertCircle, Database, Factory, Eye, EyeOff } from 'lucide-react';

const Map = dynamic(() => import('./Map'), { ssr: false });

type DataMode = 'live' | 'fixture';
type LiveFilter = 'all' | 'noaa20' | 'noaa21' | 'day' | 'night' | 'persistent' | 'mapped_industry';
type FixtureFilter = 'all' | 'industrial' | 'persistent';

export function Dashboard() {
  const [dataMode, setDataMode] = useState<DataMode>('live');
  const [hotspots, setHotspots] = useState<ThermalObservation[]>([]);
  const [selectedHotspot, setSelectedHotspot] = useState<ThermalObservation | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [persistenceMap, setPersistenceMap] = useState<Record<string, PersistenceProfileResponse>>({});

  // Phase 4 Industrial Context State
  const [industrialContextMap, setIndustrialContextMap] = useState<Record<string, IndustrialContextProfileResponse>>({});
  const [industrialFeatures, setIndustrialFeatures] = useState<OSMFeatureCollection | null>(null);
  const [industrialLayerVisible, setIndustrialLayerVisible] = useState<boolean>(true);
  const [isSyncingOSM, setIsSyncingOSM] = useState<boolean>(false);

  const [loading, setLoading] = useState(true);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Live FIRMS Metadata
  const [firmsMeta, setFirmsMeta] = useState<FIRMSHotspotsResponse | null>(null);
  const [liveFilter, setLiveFilter] = useState<LiveFilter>('all');
  const [dayRange, setDayRange] = useState<number>(1);

  // Phase 2 PostGIS Storage Metadata
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [isPostgisBacked, setIsPostgisBacked] = useState<boolean>(false);
  const [totalStored, setTotalStored] = useState<number | null>(null);
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null);

  // Phase 0 Fixture Filter
  const [fixtureFilter, setFixtureFilter] = useState<FixtureFilter>('all');

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    let isMounted = true;

    async function fetchData() {
      try {
        if (dataMode === 'live') {
          // Controlled Flow: Manual refresh syncs NASA FIRMS to PostGIS first
          if (refreshTrigger > 0) {
            setIsSyncing(true);
            try {
              const syncResp = await apiService.syncFIRMS({
                days: dayRange,
                force_refresh: true,
              });
              if (isMounted) {
                setLastSyncTime(new Date().toLocaleTimeString());
                console.log(`[Phase 2 Sync] Completed run ${syncResp.run_id} with ${syncResp.upserted_count} upserts.`);
              }
            } catch (syncErr) {
              console.warn("Sync to PostGIS failed or database unconfigured; attempting direct load:", syncErr);
            } finally {
              if (isMounted) setIsSyncing(false);
            }
          }

          // Canonical Data Path: Read observations from PostGIS storage
          let loadedFromPostGIS = false;
          try {
            const storedResp = await apiService.getStoredObservations({ limit: 1500 });
            if (!isMounted) return;

            if (storedResp && storedResp.observations && storedResp.observations.length > 0) {
              const mapped: ThermalObservation[] = storedResp.observations.map((obs) => ({
                ...obs,
                stored_in_postgis: true,
              }));
              setHotspots(mapped);
              setIsPostgisBacked(true);
              setTotalStored(storedResp.total);
              loadedFromPostGIS = true;
              setErrorMessage(null);

              const ids = mapped.map((h) => h.id).slice(0, 1500);

              // Phase 3: Fetch Batch Persistence Profiles (500 chunking)
              try {
                if (ids.length > 0) {
                  const batchRes = await apiService.getBatchPersistence(ids);
                  if (isMounted && batchRes && batchRes.profiles) {
                    setPersistenceMap(batchRes.profiles);
                  }
                }
              } catch (batchErr) {
                console.warn("[Phase 3 Batch Persistence] Warning:", batchErr);
              }

              // Phase 4: Fetch Batch Industrial Context Profiles (500 chunking)
              try {
                if (ids.length > 0) {
                  const indRes = await apiService.getBatchIndustrialContext(ids);
                  if (isMounted && indRes && indRes.profiles) {
                    setIndustrialContextMap(indRes.profiles);
                  }
                }
              } catch (indErr) {
                console.warn("[Phase 4 Batch Industrial Context] Warning:", indErr);
              }

              // Fetch Stored GeoJSON Industrial Features for map layer
              try {
                const featRes = await apiService.getOSMIndustrialFeatures({ limit: 1000 });
                if (isMounted && featRes) {
                  setIndustrialFeatures(featRes);
                }
              } catch (featErr) {
                console.warn("[Phase 4 OSM Features] Warning:", featErr);
              }
            }
          } catch (postgisErr) {
            console.warn("Could not retrieve from PostGIS storage:", postgisErr);
          }

          // Fallback if PostGIS has no records
          if (!loadedFromPostGIS) {
            const response = await apiService.getFIRMSHotspots({
              days: dayRange,
            });
            if (!isMounted) return;

            setFirmsMeta(response);
            const mapped: ThermalObservation[] = response.observations.map((obs) => ({
              ...obs,
              stored_in_postgis: false,
            }));
            setHotspots(mapped);
            setIsPostgisBacked(false);
            setErrorMessage(null);
          }
        } else {
          setHotspots([]);
          setFirmsMeta(null);
          setIsPostgisBacked(false);
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
          setIsSyncing(false);
        }
      }
    }

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [dataMode, dayRange, refreshTrigger]);

  const handleManualRefresh = () => {
    if (loading || isSyncing) return;
    setLoading(true);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleOSMSync = async () => {
    if (isSyncingOSM || hotspots.length === 0) return;
    setIsSyncingOSM(true);
    try {
      // Derive bounding box from loaded hotspots
      const lats = hotspots.map((h) => h.latitude);
      const lons = hotspots.map((h) => h.longitude);
      const minLat = Math.min(...lats) - 0.1;
      const maxLat = Math.max(...lats) + 0.1;
      const minLon = Math.min(...lons) - 0.1;
      const maxLon = Math.max(...lons) + 0.1;

      await apiService.syncOSMIndustrial({
        south: Math.max(-90, minLat),
        west: Math.max(-180, minLon),
        north: Math.min(90, maxLat),
        east: Math.min(180, maxLon),
        force_refresh: true,
      });

      // Refresh industrial features & context profiles
      const featRes = await apiService.getOSMIndustrialFeatures({ limit: 1000 });
      setIndustrialFeatures(featRes);

      const ids = hotspots.map((h) => h.id).slice(0, 1500);
      if (ids.length > 0) {
        const indRes = await apiService.getBatchIndustrialContext(ids);
        if (indRes && indRes.profiles) {
          setIndustrialContextMap(indRes.profiles);
        }
      }
    } catch (err) {
      console.error("OSM sync failed:", err);
    } finally {
      setIsSyncingOSM(false);
    }
  };

  const handleHotspotClick = async (hotspot: ThermalObservation) => {
    setSelectedHotspot(hotspot);
    setAnalysis(null);

    // Fetch persistence profile on demand if absent
    if (hotspot.id && !persistenceMap[hotspot.id]) {
      try {
        const prof = await apiService.getObservationPersistence(hotspot.id);
        if (prof) {
          setPersistenceMap(prev => ({ ...prev, [hotspot.id]: prof }));
        }
      } catch (err) {
        console.warn("Failed to fetch persistence profile on click:", err);
      }
    }

    // Fetch industrial context profile on demand if absent
    if (hotspot.id && !industrialContextMap[hotspot.id]) {
      try {
        const indProf = await apiService.getObservationIndustrialContext(hotspot.id);
        if (indProf) {
          setIndustrialContextMap(prev => ({ ...prev, [hotspot.id]: indProf }));
        }
      } catch (err) {
        console.warn("Failed to fetch industrial context profile on click:", err);
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
      if (liveFilter === 'day') return h.daynight === 'D';
      if (liveFilter === 'night') return h.daynight === 'N';
      if (liveFilter === 'persistent') return persistenceMap[h.id]?.persistence_class === 'PERSISTENT';
      if (liveFilter === 'mapped_industry') {
        const ctx = industrialContextMap[h.id]?.context_class;
        return ctx === 'STRONG' || ctx === 'MODERATE' || ctx === 'WEAK';
      }
      return true;
    } else {
      if (fixtureFilter === 'industrial') return false;
      if (fixtureFilter === 'persistent') return false;
      return true;
    }
  });

  // Calculate live counts
  const noaa20Count = hotspots.filter(h => (h.source || '').includes('NOAA20') || h.satellite === 'N20').length;
  const noaa21Count = hotspots.filter(h => (h.source || '').includes('NOAA21') || h.satellite === 'N21').length;
  const persistentCount = hotspots.filter(h => persistenceMap[h.id]?.persistence_class === 'PERSISTENT').length;
  const mappedIndustryCount = hotspots.filter(h => {
    const ctx = industrialContextMap[h.id]?.context_class;
    return ctx === 'STRONG' || ctx === 'MODERATE' || ctx === 'WEAK';
  }).length;

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
              <span className="flex items-center gap-2 text-emerald-400">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                {isPostgisBacked ? (
                  <span className="flex items-center gap-1 font-semibold">
                    <Database size={13} className="text-emerald-400" />
                    NASA FIRMS • PostGIS-backed {totalStored != null ? `(${totalStored} Stored)` : ''}
                  </span>
                ) : (
                  <span>NASA FIRMS — Live Ingestion Pipeline (VIIRS NOAA-20 & NOAA-21)</span>
                )}
                {lastSyncTime && (
                  <span className="text-[11px] text-slate-400 font-normal">
                    • Synced: {lastSyncTime}
                  </span>
                )}
              </span>
            </p>
          </div>
        </div>

        {/* Header Controls */}
        <div className="flex items-center gap-3">
          {/* Industrial Layer Toggle */}
          <button
            onClick={() => setIndustrialLayerVisible(!industrialLayerVisible)}
            className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-bold transition-all border ${
              industrialLayerVisible
                ? 'bg-cyan-950/80 border-cyan-700 text-cyan-300 shadow-sm'
                : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-white'
            }`}
            title="Toggle OpenStreetMap Industrial Layer visibility"
          >
            {industrialLayerVisible ? <Eye size={14} className="text-cyan-400" /> : <EyeOff size={14} />}
            <span>Industrial Layer: {industrialLayerVisible ? 'ON' : 'OFF'}</span>
          </button>

          {/* Sync OSM Button */}
          <button
            onClick={handleOSMSync}
            disabled={isSyncingOSM || loading}
            className="flex items-center gap-1.5 text-xs bg-cyan-900/60 hover:bg-cyan-800 border border-cyan-700 text-cyan-200 px-3 py-1.5 rounded-lg font-semibold transition-colors disabled:opacity-50"
            title="Sync server-side OpenStreetMap industrial features for current region"
          >
            <Factory size={14} className={isSyncingOSM ? 'animate-spin text-cyan-300' : 'text-cyan-400'} />
            <span>{isSyncingOSM ? 'Syncing OSM...' : 'Sync OSM'}</span>
          </button>

          {/* Refresh Button */}
          <button
            onClick={handleManualRefresh}
            disabled={loading || isSyncing}
            className="flex items-center gap-1.5 text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3 py-1.5 rounded-lg font-medium transition-colors disabled:opacity-50"
            title="Sync NASA FIRMS to PostGIS and refresh map"
          >
            <RefreshCw size={14} className={loading || isSyncing ? 'animate-spin text-orange-400' : ''} />
            <span>{isSyncing ? 'Syncing...' : loading ? 'Loading...' : 'Refresh'}</span>
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
              isLive={true}
              noaa20={noaa20Count}
              noaa21={noaa21Count}
              industrial={mappedIndustryCount}
              persistent={persistentCount}
              highRisk={0}
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
        <div className="absolute left-4 top-36 z-10 bg-white/95 backdrop-blur-sm p-3.5 rounded-xl shadow-xl pointer-events-auto border border-gray-200/80 w-60 text-xs">
          <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-gray-100">
            <h3 className="font-bold text-gray-700 uppercase tracking-wider">
              Satellite & Context Filters
            </h3>
            <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-1.5 py-0.5 rounded">
              Live PostGIS
            </span>
          </div>

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

              {/* Phase 3 Filter */}
              <label className="flex items-center gap-2 cursor-pointer font-bold text-purple-800 hover:text-purple-950 pt-1 border-t border-gray-100">
                <input
                  type="radio"
                  name="live_filter"
                  checked={liveFilter === 'persistent'}
                  onChange={() => setLiveFilter('persistent')}
                  className="accent-purple-600"
                />
                Persistent Phase 3 ({persistentCount})
              </label>

              {/* Phase 4 Filter */}
              <label className="flex items-center gap-2 cursor-pointer font-bold text-cyan-800 hover:text-cyan-950">
                <input
                  type="radio"
                  name="live_filter"
                  checked={liveFilter === 'mapped_industry'}
                  onChange={() => setLiveFilter('mapped_industry')}
                  className="accent-cyan-600"
                />
                Mapped Industry Phase 4 ({mappedIndustryCount})
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
          </div>
        </div>

        {/* Map Container */}
        <div className="flex-1 w-full relative z-0">
          <Map
            hotspots={filteredHotspots}
            persistenceMap={persistenceMap}
            industrialFeatures={industrialFeatures}
            industrialLayerVisible={industrialLayerVisible}
            onHotspotClick={handleHotspotClick}
          />
        </div>

        {/* Analysis Drawer */}
        <AnalysisDrawer 
          hotspot={selectedHotspot} 
          analysis={analysis} 
          persistenceProfile={selectedHotspot ? persistenceMap[selectedHotspot.id] : null}
          industrialContextProfile={selectedHotspot ? industrialContextMap[selectedHotspot.id] : null}
          loading={loadingAnalysis}
          onClose={handleCloseDrawer}
        />
      </div>
    </div>
  );
}
