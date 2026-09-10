"use client";

import { useEffect } from 'react';
import { MapContainer, TileLayer, LayersControl, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { ThermalObservation, PersistenceProfileResponse, OSMFeatureCollection } from '../services/api';
import { HotspotMarker } from './HotspotMarker';
import { IndustrialLayer } from './IndustrialLayer';

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: () => string })._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

interface MapProps {
  hotspots: ThermalObservation[];
  persistenceMap?: Record<string, PersistenceProfileResponse>;
  industrialFeatures?: OSMFeatureCollection | null;
  industrialLayerVisible?: boolean;
  onHotspotClick: (hotspot: ThermalObservation) => void;
}

function MapUpdater({ hotspots }: { hotspots: ThermalObservation[] }) {
  const map = useMap();
  useEffect(() => {
    if (hotspots.length > 0) {
      const bounds = L.latLngBounds(hotspots.map(h => [h.latitude, h.longitude]));
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [hotspots, map]);
  return null;
}

export default function Map({
  hotspots,
  persistenceMap,
  industrialFeatures,
  industrialLayerVisible = true,
  onHotspotClick,
}: MapProps) {
  return (
    <div className="w-full h-full relative z-0">
      <MapContainer
        center={[20.5937, 78.9629]}
        zoom={5} 
        style={{ height: '100%', width: '100%', zIndex: 0 }}
      >
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="OpenStreetMap">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Satellite">
            <TileLayer
              attribution='&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            />
          </LayersControl.BaseLayer>
        </LayersControl>
        
        {/* Phase 4 Industrial Layer (OSM Infrastructure Geometries) */}
        <IndustrialLayer data={industrialFeatures || null} visible={industrialLayerVisible} />

        {/* Phase 3 Canonical Thermal Observation Markers */}
        {hotspots.map((hotspot) => (
          <HotspotMarker 
            key={hotspot.id} 
            hotspot={hotspot} 
            profile={persistenceMap?.[hotspot.id]}
            onClick={onHotspotClick} 
          />
        ))}

        <MapUpdater hotspots={hotspots} />
      </MapContainer>

      {/* Map Intelligence Legend */}
      <div className="absolute bottom-4 left-[260px] lg:left-[270px] z-[1000] pointer-events-auto bg-slate-900/90 backdrop-blur-md border border-slate-700/60 rounded-xl p-3 shadow-2xl text-xs text-slate-200 select-none space-y-3">
        <div>
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span>
            Phase 3 — Temporal Persistence
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <div className="relative w-5 h-5 flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border-[2.5px] border-purple-500 bg-purple-500/25 shadow-[0_0_8px_rgba(168,85,247,0.8)]"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-orange-500 border border-white"></div>
              </div>
              <span className="text-[11px] font-semibold text-purple-200">Persistent Thermal</span>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="relative w-5 h-5 flex items-center justify-center">
                <div className="absolute inset-0.5 rounded-full border-[1.5px] border-dashed border-purple-400 bg-purple-500/15"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-orange-500 border border-white"></div>
              </div>
              <span className="text-[11px] text-slate-300">Recurring Thermal</span>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="w-5 h-5 flex items-center justify-center">
                <div className="w-3 h-3 rounded-full bg-orange-500 border-2 border-white shadow-sm"></div>
              </div>
              <span className="text-[11px] text-slate-300">Thermal Detection</span>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-800 pt-2">
          <div className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
            Phase 4 — Mapped Industrial Context
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <div className="w-5 h-5 flex items-center justify-center">
                <div className="w-3 h-3 rounded-full bg-cyan-500 border border-white shadow-sm"></div>
              </div>
              <span className="text-[11px] text-cyan-200">OSM Industrial Facility</span>
            </div>
            <div className="flex items-center gap-2.5">
              <div className="w-5 h-5 flex items-center justify-center">
                <div className="w-4 h-3 rounded border border-dashed border-cyan-400 bg-cyan-500/20"></div>
              </div>
              <span className="text-[11px] text-cyan-300">Industrial Area / Polygon</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
