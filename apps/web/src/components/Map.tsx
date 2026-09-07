"use client";

import { useEffect } from 'react';
import { MapContainer, TileLayer, LayersControl, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Hotspot } from '../services/api';
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

export default function Map({ hotspots, onHotspotClick }: MapProps) {
  return (
    <div className="w-full h-full z-0">
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
            onClick={onHotspotClick} 
          />
        ))}

        <MapUpdater hotspots={hotspots} />
      </MapContainer>
    </div>
  );
}
