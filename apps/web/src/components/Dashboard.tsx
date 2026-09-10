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
  LandCoverProfileResponse,
  SentinelContextProfileResponse,
  FusionProfileResponse,
  ClassificationPredictionResponse,
  LocalExplanationResponse,
  GlobalExplanationResponse,
  OSMFeatureCollection,
} from '../services/api';
import { StatsCards } from './StatsCards';
import { AnalysisDrawer } from './AnalysisDrawer';
import { GlobalExplainabilityModal } from './GlobalExplainabilityModal';
import {
  Activity,
  RefreshCw,
  AlertCircle,
  Database,
  Factory,
  Eye,
  EyeOff,
  Trees,
  Satellite,
  Layers,
  BrainCircuit,
  Sparkles,
  BarChart3,
} from 'lucide-react';

const Map = dynamic(() => import('./Map'), { ssr: false });

type DataMode = 'live' | 'fixture';
type LiveFilter = 'all' | 'noaa20' | 'noaa21' | 'day' | 'night' | 'persistent' | 'mapped_industry';
type LandCoverFilter = 'all' | 'cropland' | 'tree_cover' | 'built_up' | 'grassland' | 'mixed';
type SentinelFilter = 'all' | 'evaluated' | 'clear' | 'cloud_limited' | 'recent';
type FusionFilter = 'all' | 'complete' | 'partial' | 'evaluated';
type ClassificationFilter = 'all' | 'industrial' | 'agricultural' | 'natural' | 'built_non_industrial' | 'mixed' | 'insufficient';
type ExplanationFilter = 'all' | 'available' | 'insufficient' | 'tree_shap';
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

  // Phase 5 Land-Cover Context State
  const [landCoverMap, setLandCoverMap] = useState<Record<string, LandCoverProfileResponse>>({});
  const [isSyncingLandCover, setIsSyncingLandCover] = useState<boolean>(false);
  const [landCoverFilter, setLandCoverFilter] = useState<LandCoverFilter>('all');

  // Phase 6 Sentinel-2 Satellite Context State
  const [sentinelContextMap, setSentinelContextMap] = useState<Record<string, SentinelContextProfileResponse>>({});
  const [isSyncingSentinel, setIsSyncingSentinel] = useState<boolean>(false);
  const [sentinelFilter, setSentinelFilter] = useState<SentinelFilter>('all');

  // Phase 7 Feature Fusion State
  const [fusionMap, setFusionMap] = useState<Record<string, FusionProfileResponse>>({});
  const [isSyncingFusion, setIsSyncingFusion] = useState<boolean>(false);
  const [fusionFilter, setFusionFilter] = useState<FusionFilter>('all');

  // Phase 8 Intelligent Classification State
  const [classificationMap, setClassificationMap] = useState<Record<string, ClassificationPredictionResponse>>({});
  const [isSyncingClassification, setIsSyncingClassification] = useState<boolean>(false);
  const [classificationFilter, setClassificationFilter] = useState<ClassificationFilter>('all');

  // Phase 9 Model Explainability State
  const [explanationMap, setExplanationMap] = useState<Record<string, LocalExplanationResponse>>({});
  const [isSyncingExplanation, setIsSyncingExplanation] = useState<boolean>(false);
  const [explanationFilter, setExplanationFilter] = useState<ExplanationFilter>('all');
  const [isGlobalModalOpen, setIsGlobalModalOpen] = useState<boolean>(false);
  const [globalExplanationData, setGlobalExplanationData] = useState<GlobalExplanationResponse | null>(null);
  const [loadingGlobalExplanation, setLoadingGlobalExplanation] = useState<boolean>(false);


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

              // Concurrently fetch intelligence layers with strict state isolation
              if (ids.length > 0) {
                await Promise.allSettled([
                  // Phase 3: Batch Persistence Profiles (500 chunking)
                  apiService.getBatchPersistence(ids)
                    .then((batchRes) => {
                      if (isMounted && batchRes?.profiles) {
                        setPersistenceMap(batchRes.profiles);
                      }
                    })
                    .catch((err) => console.warn("[Phase 3 Batch Persistence] Warning:", err)),

                  // Phase 4: Batch Industrial Context Profiles (500 chunking)
                  apiService.getBatchIndustrialContext(ids)
                    .then((indRes) => {
                      if (isMounted && indRes?.profiles) {
                        setIndustrialContextMap(indRes.profiles);
                      }
                    })
                    .catch((err) => console.warn("[Phase 4 Batch Industrial Context] Warning:", err)),

                  // Phase 4: Stored GeoJSON Industrial Features for map layer
                  apiService.getOSMIndustrialFeatures({ limit: 1000 })
                    .then((featRes) => {
                      if (isMounted && featRes) {
                        setIndustrialFeatures(featRes);
                      }
                    })
                    .catch((err) => console.warn("[Phase 4 OSM Features] Warning:", err)),

                  // Phase 5: Batch Land-Cover Profiles (500 chunking)
                  apiService.getBatchLandCover(ids)
                    .then((lcRes) => {
                      if (isMounted && lcRes?.profiles) {
                        setLandCoverMap(lcRes.profiles);
                      }
                    })
                    .catch((err) => console.warn("[Phase 5 Batch Land Cover] Warning:", err)),

                  // Phase 6: Batch Sentinel-2 Context Profiles (500 chunking)
                  apiService.getBatchSentinelContext(ids)
                    .then((sentRes) => {
                      if (isMounted && sentRes?.profiles) {
                        setSentinelContextMap(sentRes.profiles);
                      }
                    })
                    .catch((err) => console.warn("[Phase 6 Batch Sentinel Context] Warning:", err)),

                  // Phase 7: Batch Feature Fusion Profiles (500 chunking)
                  apiService.getBatchFusion(ids)
                    .then((fusRes) => {
                      if (isMounted && fusRes?.profiles) {
                        setFusionMap(fusRes.profiles);
                      }
                    })
                    .catch((err) => console.warn("[Phase 7 Batch Fusion] Warning:", err)),

                  // Phase 8: Batch Classification Predictions (500 chunking)
                  apiService.getBatchClassifications(ids)
                    .then((classRes) => {
                      if (isMounted && classRes?.predictions) {
                        setClassificationMap(classRes.predictions);
                      }
                    })
                    .catch((err) => console.warn("[Phase 8 Batch Classification] Warning:", err)),

                  // Phase 9: Batch Explainability Profiles (500 chunking)
                  apiService.getBatchExplanations(ids)
                    .then((expRes) => {
                      if (isMounted && expRes?.explanations) {
                        setExplanationMap(expRes.explanations);
                      }
                    })
                    .catch((err) => console.warn("[Phase 9 Batch Explainability] Warning:", err)),
                ]);
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

  const handleLandCoverSync = async () => {
    if (isSyncingLandCover || hotspots.length === 0) return;
    setIsSyncingLandCover(true);
    try {
      const ids = hotspots.map((h) => h.id).slice(0, 1500);
      await apiService.syncLandCover({
        observation_ids: ids,
        limit: 1500,
        force_recompute: false,
      });

      // Refresh land-cover profiles
      if (ids.length > 0) {
        const lcRes = await apiService.getBatchLandCover(ids);
        if (lcRes && lcRes.profiles) {
          setLandCoverMap(lcRes.profiles);
        }
      }
    } catch (err) {
      console.error("Land-cover sync failed:", err);
    } finally {
      setIsSyncingLandCover(false);
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

    // Fetch land-cover profile on demand if absent
    if (hotspot.id && !landCoverMap[hotspot.id]) {
      try {
        const lcProf = await apiService.getObservationLandCover(hotspot.id);
        if (lcProf) {
          setLandCoverMap(prev => ({ ...prev, [hotspot.id]: lcProf }));
        }
      } catch (err) {
        console.warn("Failed to fetch land cover profile on click:", err);
      }
    }

    // Fetch Sentinel-2 profile on demand if absent
    if (hotspot.id && !sentinelContextMap[hotspot.id]) {
      try {
        const sentProf = await apiService.getObservationSentinelContext(hotspot.id);
        if (sentProf) {
          setSentinelContextMap(prev => ({ ...prev, [hotspot.id]: sentProf }));
        }
      } catch (err) {
        console.warn("Failed to fetch Sentinel profile on click:", err);
      }
    }

    // Fetch Feature Fusion profile on demand if absent
    if (hotspot.id && !fusionMap[hotspot.id]) {
      try {
        const fusProf = await apiService.getObservationFusion(hotspot.id);
        if (fusProf) {
          setFusionMap(prev => ({ ...prev, [hotspot.id]: fusProf }));
        }
      } catch (err) {
        console.warn("Failed to fetch fusion profile on click:", err);
      }
    }

    // Fetch Phase 8 Classification prediction on demand if absent
    if (hotspot.id && !classificationMap[hotspot.id]) {
      try {
        const classProf = await apiService.getObservationClassification(hotspot.id);
        if (classProf) {
          setClassificationMap(prev => ({ ...prev, [hotspot.id]: classProf }));
        }
      } catch (err) {
        console.warn("Failed to fetch classification prediction on click:", err);
      }
    }

    // Fetch Phase 9 Explanation on demand if absent
    if (hotspot.id && !explanationMap[hotspot.id]) {
      try {
        const expProf = await apiService.getObservationExplanation(hotspot.id);
        if (expProf) {
          setExplanationMap(prev => ({ ...prev, [hotspot.id]: expProf }));
        }
      } catch (err) {
        console.warn("Failed to fetch explanation on click:", err);
      }
    }
  };

  const handleSyncSentinel = async (targetId?: string) => {
    if (isSyncingSentinel) return;
    setIsSyncingSentinel(true);
    try {
      const idsToSync = targetId
        ? [targetId]
        : filteredHotspots.slice(0, 25).map((h) => h.id);
      if (idsToSync.length === 0) return;

      const res = await apiService.syncSentinelContext({
        observation_ids: idsToSync,
        force_refresh: false,
      });
      if (res.profiles) {
        setSentinelContextMap(prev => ({ ...prev, ...res.profiles }));
      }
    } catch (err) {
      console.error("Sentinel sync failed:", err);
    } finally {
      setIsSyncingSentinel(false);
    }
  };

  const handleSyncFusion = async () => {
    if (isSyncingFusion || hotspots.length === 0) return;
    setIsSyncingFusion(true);
    try {
      const ids = hotspots.map((h) => h.id).slice(0, 1500);
      await apiService.syncFusion({
        observation_ids: ids,
        force_recompute: false,
      });

      // Refresh fusion profiles via 500-chunked batch
      if (ids.length > 0) {
        const res = await apiService.getBatchFusion(ids);
        if (res && res.profiles) {
          setFusionMap(res.profiles);
        }
      }
    } catch (err) {
      console.error("Feature Fusion sync failed:", err);
    } finally {
      setIsSyncingFusion(false);
    }
  };

  const handleSyncClassification = async () => {
    if (isSyncingClassification || hotspots.length === 0) return;
    setIsSyncingClassification(true);
    try {
      const ids = hotspots.map((h) => h.id).slice(0, 1500);
      await apiService.syncClassifications({
        observation_ids: ids,
        force_recompute: true,
      });

      // Refresh batch predictions via 500-chunked batch
      if (ids.length > 0) {
        const res = await apiService.getBatchClassifications(ids);
        if (res && res.predictions) {
          setClassificationMap(res.predictions);
        }
      }
    } catch (err) {
      console.error("Classification sync failed:", err);
    } finally {
      setIsSyncingClassification(false);
    }
  };

  const handleSyncExplanation = async () => {
    if (isSyncingExplanation || hotspots.length === 0) return;
    setIsSyncingExplanation(true);
    try {
      const ids = hotspots.map((h) => h.id).slice(0, 1500);
      await apiService.syncExplanations({
        observation_ids: ids,
        force_recompute: true,
      });

      // Refresh batch explanations via 500-chunked batch
      if (ids.length > 0) {
        const res = await apiService.getBatchExplanations(ids);
        if (res && res.explanations) {
          setExplanationMap(res.explanations);
        }
      }
    } catch (err) {
      console.error("Explanation sync failed:", err);
    } finally {
      setIsSyncingExplanation(false);
    }
  };

  const handleSyncSingleExplanation = async (obsId: string) => {
    try {
      await apiService.syncExplanations({
        observation_ids: [obsId],
        force_recompute: true,
      });
      const single = await apiService.getObservationExplanation(obsId);
      if (single) {
        setExplanationMap(prev => ({ ...prev, [obsId]: single }));
      }
    } catch (err) {
      console.error("Single observation explanation sync failed:", err);
    }
  };

  const handleOpenGlobalModal = async () => {
    setIsGlobalModalOpen(true);
    if (!globalExplanationData) {
      setLoadingGlobalExplanation(true);
      try {
        const data = await apiService.getGlobalExplanation();
        setGlobalExplanationData(data);
      } catch (err) {
        console.error("Failed to load global explanation:", err);
      } finally {
        setLoadingGlobalExplanation(false);
      }
    }
  };

  const handleCloseDrawer = () => {
    setSelectedHotspot(null);
    setAnalysis(null);
  };

  // Filtered hotspots with composed filters
  const filteredHotspots = hotspots.filter((h) => {
    if (dataMode === 'live') {
      let matchesBase = true;
      if (liveFilter === 'noaa20') matchesBase = (h.source || '').includes('NOAA20') || h.satellite === 'N20';
      else if (liveFilter === 'noaa21') matchesBase = (h.source || '').includes('NOAA21') || h.satellite === 'N21';
      else if (liveFilter === 'day') matchesBase = h.daynight === 'D';
      else if (liveFilter === 'night') matchesBase = h.daynight === 'N';
      else if (liveFilter === 'persistent') matchesBase = persistenceMap[h.id]?.persistence_class === 'PERSISTENT';
      else if (liveFilter === 'mapped_industry') {
        const ctx = industrialContextMap[h.id]?.context_class;
        matchesBase = ctx === 'STRONG' || ctx === 'MODERATE' || ctx === 'WEAK';
      }
      if (!matchesBase) return false;

      // Phase 5 Land-Cover Filter
      if (landCoverFilter === 'cropland') {
        return landCoverMap[h.id]?.context_class === 'CROPLAND_DOMINANT';
      } else if (landCoverFilter === 'tree_cover') {
        return landCoverMap[h.id]?.context_class === 'TREE_COVER_DOMINANT';
      } else if (landCoverFilter === 'built_up') {
        return landCoverMap[h.id]?.context_class === 'BUILT_UP_DOMINANT';
      } else if (landCoverFilter === 'grassland') {
        return landCoverMap[h.id]?.context_class === 'GRASSLAND_DOMINANT';
      } else if (landCoverFilter === 'mixed') {
        return landCoverMap[h.id]?.context_class === 'MIXED';
      }

      // Phase 6 Sentinel-2 Context Filter
      if (sentinelFilter === 'evaluated') {
        const prof = sentinelContextMap[h.id];
        if (!prof || prof.provider_status === 'NOT_EVALUATED' || prof.provider_status === 'ERROR' || prof.provider_status === 'PROVIDER_UNAVAILABLE') {
          return false;
        }
      } else if (sentinelFilter === 'clear') {
        const prof = sentinelContextMap[h.id];
        if (!prof || (prof.quality_status !== 'EXCELLENT' && prof.quality_status !== 'GOOD')) {
          return false;
        }
      } else if (sentinelFilter === 'cloud_limited') {
        const prof = sentinelContextMap[h.id];
        if (!prof || prof.quality_status !== 'CLOUD_LIMITED') {
          return false;
        }
      } else if (sentinelFilter === 'recent') {
        const prof = sentinelContextMap[h.id];
        if (!prof || (prof.temporal_quality !== 'FRESH' && prof.temporal_quality !== 'RECENT')) {
          return false;
        }
      }

      // Phase 7 Feature Fusion Filter
      if (fusionFilter === 'complete') {
        return fusionMap[h.id]?.fusion_status === 'COMPLETE';
      } else if (fusionFilter === 'partial') {
        return fusionMap[h.id]?.fusion_status === 'PARTIAL';
      } else if (fusionFilter === 'evaluated') {
        return Boolean(fusionMap[h.id]);
      }

      // Phase 8 Intelligent Classification Filter
      if (classificationFilter === 'insufficient') {
        return classificationMap[h.id]?.classification_status === 'INSUFFICIENT_EVIDENCE';
      } else if (classificationFilter === 'industrial') {
        return classificationMap[h.id]?.predicted_class === 'INDUSTRIAL_THERMAL_CONTEXT';
      } else if (classificationFilter === 'agricultural') {
        return classificationMap[h.id]?.predicted_class === 'AGRICULTURAL_THERMAL_CONTEXT';
      } else if (classificationFilter === 'natural') {
        return classificationMap[h.id]?.predicted_class === 'NATURAL_VEGETATION_THERMAL_CONTEXT';
      } else if (classificationFilter === 'built_non_industrial') {
        return classificationMap[h.id]?.predicted_class === 'BUILT_NON_INDUSTRIAL_CONTEXT';
      } else if (classificationFilter === 'mixed') {
        return classificationMap[h.id]?.predicted_class === 'MIXED_THERMAL_CONTEXT';
      }

      // Phase 9 Model Explainability Filter
      if (explanationFilter === 'available') {
        const exp = explanationMap[h.id];
        return exp?.explanation_status === 'AVAILABLE';
      } else if (explanationFilter === 'insufficient') {
        const exp = explanationMap[h.id];
        return exp?.explanation_status === 'INSUFFICIENT_EVIDENCE';
      } else if (explanationFilter === 'tree_shap') {
        const exp = explanationMap[h.id];
        return exp?.method?.toLowerCase().includes('tree') ?? false;
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
  const landCoverEvaluatedCount = hotspots.filter(h => {
    const prof = landCoverMap[h.id];
    return prof && prof.coverage_status !== 'UNAVAILABLE';
  }).length;
  const sentinelEvaluatedCount = hotspots.filter(h => {
    const prof = sentinelContextMap[h.id];
    return prof && (prof.provider_status === 'AVAILABLE' || prof.provider_status === 'CLOUD_LIMITED');
  }).length;
  const sentinelClearCount = hotspots.filter(h => {
    const prof = sentinelContextMap[h.id];
    return prof && (prof.quality_status === 'EXCELLENT' || prof.quality_status === 'GOOD');
  }).length;
  const fusionCompleteCount = hotspots.filter(h => fusionMap[h.id]?.fusion_status === 'COMPLETE').length;
  const fusionPartialCount = hotspots.filter(h => fusionMap[h.id]?.fusion_status === 'PARTIAL').length;
  const fusionEvaluatedCount = hotspots.filter(h => Boolean(fusionMap[h.id])).length;
  const classificationCount = Object.keys(classificationMap).length;
  const classificationIndustrialCount = Object.values(classificationMap).filter(p => p.predicted_class === 'INDUSTRIAL_THERMAL_CONTEXT').length;
  const classificationAgCount = Object.values(classificationMap).filter(p => p.predicted_class === 'AGRICULTURAL_THERMAL_CONTEXT').length;
  const classificationNatCount = Object.values(classificationMap).filter(p => p.predicted_class === 'NATURAL_VEGETATION_THERMAL_CONTEXT').length;
  const classificationBuiltCount = Object.values(classificationMap).filter(p => p.predicted_class === 'BUILT_NON_INDUSTRIAL_CONTEXT').length;
  const classificationMixedCount = Object.values(classificationMap).filter(p => p.predicted_class === 'MIXED_THERMAL_CONTEXT').length;
  const classificationInsufficientCount = Object.values(classificationMap).filter(p => p.classification_status === 'INSUFFICIENT_EVIDENCE').length;
  const explanationCount = Object.keys(explanationMap).length;
  const explanationAvailableCount = Object.values(explanationMap).filter(e => e.explanation_status === 'AVAILABLE').length;
  const explanationInsufficientCount = Object.values(explanationMap).filter(e => e.explanation_status === 'INSUFFICIENT_EVIDENCE').length;
  const explanationTreeCount = Object.values(explanationMap).filter(e => e.method?.toLowerCase().includes('tree')).length;

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
        <div className="flex items-center gap-2.5">
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

          {/* Sync Land Cover Button */}
          <button
            onClick={handleLandCoverSync}
            disabled={isSyncingLandCover || loading}
            className="flex items-center gap-1.5 text-xs bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-700 text-emerald-300 px-3 py-1.5 rounded-lg font-semibold transition-colors disabled:opacity-50"
            title="Precompute / sync ESA WorldCover baseline land-cover profiles"
          >
            <Trees size={14} className={isSyncingLandCover ? 'animate-spin text-emerald-300' : 'text-emerald-400'} />
            <span>{isSyncingLandCover ? 'Syncing Land Cover...' : 'Sync Land Cover'}</span>
          </button>

          {/* Sync Sentinel-2 Button */}
          <button
            onClick={() => handleSyncSentinel()}
            disabled={isSyncingSentinel || loading}
            className="flex items-center gap-1.5 text-xs bg-indigo-950/80 hover:bg-indigo-900 border border-indigo-700 text-indigo-300 px-3 py-1.5 rounded-lg font-semibold transition-colors disabled:opacity-50"
            title="Precompute / sync Sentinel-2 L2A optical/SWIR context profiles for top 25 observations"
          >
            <Satellite size={14} className={isSyncingSentinel ? 'animate-spin text-indigo-300' : 'text-indigo-400'} />
            <span>{isSyncingSentinel ? 'Syncing Sentinel...' : 'Sync Sentinel'}</span>
          </button>

          {/* Sync Feature Fusion Button */}
          <button
            onClick={handleSyncFusion}
            disabled={isSyncingFusion || loading}
            className="flex items-center gap-1.5 text-xs bg-purple-950/80 hover:bg-purple-900 border border-purple-700 text-purple-300 px-3 py-1.5 rounded-lg font-semibold transition-colors disabled:opacity-50"
            title="Assemble & persist Phase 7 multi-modal feature fusion profiles"
          >
            <Layers size={14} className={isSyncingFusion ? 'animate-spin text-purple-300' : 'text-purple-400'} />
            <span>{isSyncingFusion ? 'Syncing Fusion...' : 'Sync Fusion'}</span>
          </button>

          {/* Sync Classification Button */}
          <button
            onClick={handleSyncClassification}
            disabled={isSyncingClassification || loading}
            className="flex items-center gap-1.5 text-xs bg-rose-950/80 hover:bg-rose-900 border border-rose-700 text-rose-300 px-3 py-1.5 rounded-lg font-semibold transition-colors disabled:opacity-50"
            title="Classify & persist Phase 8 thermal context archetypes via ML inference"
          >
            <BrainCircuit size={14} className={isSyncingClassification ? 'animate-spin text-rose-300' : 'text-rose-400'} />
            <span>{isSyncingClassification ? 'Classifying...' : 'Sync Classify'}</span>
          </button>

          {/* Sync Explainability Button (Phase 9) */}
          <button
            onClick={handleSyncExplanation}
            disabled={isSyncingExplanation || loading}
            className="flex items-center gap-1.5 text-xs bg-amber-950/80 hover:bg-amber-900 border border-amber-700 text-amber-300 px-3 py-1.5 rounded-lg font-semibold transition-colors disabled:opacity-50"
            title="Compute & persist Phase 9 TreeSHAP local feature attributions"
          >
            <Sparkles size={14} className={isSyncingExplanation ? 'animate-spin text-amber-300' : 'text-amber-400'} />
            <span>{isSyncingExplanation ? 'Explaining...' : 'Sync SHAP'}</span>
          </button>

          {/* Global Explainability Insights Button */}
          <button
            onClick={handleOpenGlobalModal}
            className="flex items-center gap-1.5 text-xs bg-slate-900 hover:bg-slate-800 border border-amber-500/60 text-amber-300 px-3 py-1.5 rounded-lg font-bold transition-all shadow-xs"
            title="View global permutation feature importance across model"
          >
            <BarChart3 size={14} className="text-amber-400" />
            <span>Global SHAP</span>
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
              landCoverEvaluated={landCoverEvaluatedCount}
              sentinelEvaluated={sentinelEvaluatedCount}
              sentinelClear={sentinelClearCount}
              fusionComplete={fusionCompleteCount}
              fusionPartial={fusionPartialCount}
              classificationCount={classificationCount}
              classificationIndustrial={classificationIndustrialCount}
              explanationCount={explanationCount}
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
        <div className="absolute left-4 top-36 z-10 bg-white/95 backdrop-blur-sm p-3.5 pb-3 rounded-xl shadow-xl pointer-events-auto border border-gray-200/80 w-60 text-xs max-h-[calc(100vh-140px)] overflow-y-auto overflow-x-hidden pr-1">
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

            {/* Phase 5 Land-Cover Filter */}
            <div className="pt-2.5 border-t border-gray-100">
              <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block mb-1.5 flex items-center gap-1">
                <Trees size={12} className="text-emerald-600" /> Land-Cover Filter (Phase 5)
              </span>
              <div className="grid grid-cols-2 gap-1 text-[11px]">
                {[
                  { id: 'all', label: 'All Covers' },
                  { id: 'cropland', label: 'Cropland' },
                  { id: 'tree_cover', label: 'Tree Cover' },
                  { id: 'built_up', label: 'Built-up' },
                  { id: 'grassland', label: 'Grassland' },
                  { id: 'mixed', label: 'Mixed' },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setLandCoverFilter(opt.id as LandCoverFilter)}
                    className={`py-1 px-1.5 rounded text-left font-medium transition-all ${
                      landCoverFilter === opt.id
                        ? 'bg-emerald-700 text-white font-bold shadow-xs'
                        : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Phase 6 Sentinel-2 Filter */}
            <div className="pt-2.5 border-t border-gray-100">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-bold text-indigo-800 uppercase tracking-wider flex items-center gap-1">
                  <Satellite size={12} className="text-indigo-600" /> Sentinel-2 (Phase 6)
                </span>
                <span className="text-[9px] font-semibold text-indigo-600">
                  {sentinelEvaluatedCount} Evaluated
                </span>
              </div>
              <div className="grid grid-cols-2 gap-1 text-[11px]">
                {[
                  { id: 'all', label: 'All' },
                  { id: 'evaluated', label: 'Evaluated' },
                  { id: 'clear', label: 'Clear / Good' },
                  { id: 'cloud_limited', label: 'Cloud Limited' },
                  { id: 'recent', label: 'Recent Context' },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setSentinelFilter(opt.id as SentinelFilter)}
                    className={`py-1 px-1.5 rounded text-left font-medium transition-all ${
                      sentinelFilter === opt.id
                        ? 'bg-indigo-700 text-white font-bold shadow-xs'
                        : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Phase 7 Feature Fusion Filter */}
            <div className="pt-2.5 border-t border-gray-100">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-bold text-purple-800 uppercase tracking-wider flex items-center gap-1">
                  <Layers size={12} className="text-purple-600" /> Feature Fusion (Phase 7)
                </span>
                <span className="text-[9px] font-semibold text-purple-600">
                  {fusionEvaluatedCount} Evaluated
                </span>
              </div>
              <div className="grid grid-cols-2 gap-1 text-[11px]">
                {[
                  { id: 'all', label: 'All' },
                  { id: 'complete', label: `Complete (${fusionCompleteCount})` },
                  { id: 'partial', label: `Partial (${fusionPartialCount})` },
                  { id: 'evaluated', label: 'Evaluated' },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setFusionFilter(opt.id as FusionFilter)}
                    className={`py-1 px-1.5 rounded text-left font-medium transition-all ${
                      fusionFilter === opt.id
                        ? 'bg-purple-700 text-white font-bold shadow-xs'
                        : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Phase 8 Intelligent Classification Filter */}
            <div className="pt-2.5 border-t border-gray-100">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1">
                  <BrainCircuit size={12} className="text-rose-600" /> Classification (Phase 8)
                </span>
                <span className="text-[9px] font-semibold text-rose-600">
                  {classificationCount} Classified
                </span>
              </div>
              <div className="grid grid-cols-2 gap-1 text-[11px]">
                {[
                  { id: 'all', label: 'All Classes' },
                  { id: 'industrial', label: `Industrial (${classificationIndustrialCount})` },
                  { id: 'agricultural', label: `Ag (${classificationAgCount})` },
                  { id: 'natural', label: `Natural (${classificationNatCount})` },
                  { id: 'built_non_industrial', label: `Built (${classificationBuiltCount})` },
                  { id: 'mixed', label: `Mixed (${classificationMixedCount})` },
                  { id: 'insufficient', label: `Insufficient (${classificationInsufficientCount})` },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setClassificationFilter(opt.id as ClassificationFilter)}
                    className={`py-1 px-1.5 rounded text-left font-medium transition-all ${
                      opt.id === 'insufficient' ? 'col-span-2' : ''
                    } ${
                      classificationFilter === opt.id
                        ? 'bg-rose-700 text-white font-bold shadow-xs'
                        : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Phase 9 Model Explainability Filter */}
            <div className="pt-2.5 border-t border-gray-100">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider flex items-center gap-1">
                  <Sparkles size={12} className="text-amber-600" /> Explainability (Phase 9)
                </span>
                <span className="text-[9px] font-semibold text-amber-700">
                  {explanationCount} Explained
                </span>
              </div>
              <div className="grid grid-cols-2 gap-1 text-[11px]">
                {[
                  { id: 'all', label: 'All Explanations' },
                  { id: 'available', label: `Available (${explanationAvailableCount})` },
                  { id: 'tree_shap', label: `TreeSHAP (${explanationTreeCount})` },
                  { id: 'insufficient', label: `Insufficient (${explanationInsufficientCount})` },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setExplanationFilter(opt.id as ExplanationFilter)}
                    className={`py-1 px-1.5 rounded text-left font-medium transition-all ${
                      explanationFilter === opt.id
                        ? 'bg-amber-700 text-white font-bold shadow-xs'
                        : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
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
          landCoverProfile={selectedHotspot ? landCoverMap[selectedHotspot.id] : null}
          sentinelProfile={selectedHotspot ? sentinelContextMap[selectedHotspot.id] : null}
          fusionProfile={selectedHotspot ? fusionMap[selectedHotspot.id] : null}
          classificationProfile={selectedHotspot ? classificationMap[selectedHotspot.id] : null}
          explanationProfile={selectedHotspot ? explanationMap[selectedHotspot.id] : null}
          loading={loadingAnalysis}
          onClose={handleCloseDrawer}
          onSyncSentinel={handleSyncSentinel}
          onSyncExplanation={handleSyncSingleExplanation}
        />

        {/* Global Explainability Modal */}
        <GlobalExplainabilityModal
          isOpen={isGlobalModalOpen}
          onClose={() => setIsGlobalModalOpen(false)}
          data={globalExplanationData}
          loading={loadingGlobalExplanation}
        />
      </div>
    </div>
  );
}
