"use client";

import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { Hotspot } from '../services/api';

// Create a custom icon for hotspots
const createHotspotIcon = (confidence: string) => {
  const color = confidence === 'high' ? 'red' : confidence === 'nominal' ? 'orange' : 'yellow';
  
  return L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="background-color:${color}; width:15px; height:15px; border-radius:50%; border:2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5);"></div>`,
    iconSize: [15, 15],
    iconAnchor: [7.5, 7.5]
  });
};

interface HotspotMarkerProps {
  hotspot: Hotspot;
  onClick: (hotspot: Hotspot) => void;
}

export function HotspotMarker({ hotspot, onClick }: HotspotMarkerProps) {
  return (
    <Marker 
      position={[hotspot.latitude, hotspot.longitude]} 
      icon={createHotspotIcon(hotspot.confidence)}
      eventHandlers={{
        click: () => onClick(hotspot)
      }}
    >
      <Popup>
        <div className="text-sm">
          <strong>FRP:</strong> {hotspot.frp_mw} MW<br/>
          <strong>Confidence:</strong> {hotspot.confidence}<br/>
          <strong>Date:</strong> {new Date(hotspot.acquired_at).toLocaleDateString()}<br/>
          <button 
            className="mt-2 text-xs bg-blue-600 text-white px-2 py-1 rounded"
            onClick={(e) => {
              e.stopPropagation();
              onClick(hotspot);
            }}
          >
            Analyze Location
          </button>
        </div>
      </Popup>
    </Marker>
  );
}
