"use client";

import { useEffect } from 'react';
import { MapContainer, TileLayer, LayersControl, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Hotspot, PersistenceProfileResponse } from '../services/api';
import { HotspotMarker } from './HotspotMarker';

// Fix Leaflet's default icon path issues in Next.js
delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: () => string })._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

interface MapProps {
  hotspots: Hotspot[];
  persistenceMap?: Record<string, PersistenceProfileResponse>;
  onHotspotClick: (hotspot: Hotspot) => void;
}

function MapUpdater({ hotspots }: { hotspots: Hotspot[] }) {
  const map = useMap();
  useEffect(() => {
    if (hotspots.length > 0) {
      const bounds = L.latLngBounds(hotspots.map(h => [h.latitude, h.longitude]));
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [hotspots, map]);
  return null;
}

export default function Map({ hotspots, persistenceMap, onHotspotClick }: MapProps) {
  return (
    <div className="w-full h-full relative z-0">
      <MapContainer 
        center={[20.5937, 78.9629]} // Default to India
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

      {/* Phase 3 Thermal Intelligence Map Legend */}
      <div className="absolute bottom-6 left-6 z-[1000] pointer-events-auto bg-slate-900/90 backdrop-blur-md border border-slate-700/60 rounded-xl p-3 shadow-2xl text-xs text-slate-200 select-none">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span>
          Thermal Intelligence
        </div>
        <div className="space-y-2">
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

          <div className="flex items-center gap-2.5">
            <div className="w-5 h-5 flex items-center justify-center">
              <div className="w-3 h-3 rounded-full bg-orange-500 border-2 border-slate-400 shadow-sm"></div>
            </div>
            <span className="text-[11px] text-slate-400">Insufficient History</span>
          </div>
        </div>
      </div>
    </div>
  );
}
