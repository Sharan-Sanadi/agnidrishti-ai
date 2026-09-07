"use client";

import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { Hotspot } from '../services/api';

// Create a custom icon for hotspots
const createHotspotIcon = (confidence: string) => {
  const conf = confidence.toLowerCase();
  const color = (conf === 'high' || conf === 'h') ? '#ef4444' : (conf === 'nominal' || conf === 'n') ? '#f97316' : '#eab308';
  
  return L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="background-color:${color}; width:16px; height:16px; border-radius:50%; border:2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.6);"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });
};

interface HotspotMarkerProps {
  hotspot: Hotspot;
  onClick: (hotspot: Hotspot) => void;
}

export function HotspotMarker({ hotspot, onClick }: HotspotMarkerProps) {
  const conf = hotspot.confidence.toLowerCase();
  const confLabel = conf === 'h' ? 'High' : conf === 'n' ? 'Nominal' : conf === 'l' ? 'Low' : hotspot.confidence;
  const frpDisplay = hotspot.frp_mw != null ? `${hotspot.frp_mw} MW` : 'N/A';

  return (
    <Marker 
      position={[hotspot.latitude, hotspot.longitude]} 
      icon={createHotspotIcon(hotspot.confidence)}
      eventHandlers={{
        click: () => onClick(hotspot)
      }}
    >
      <Popup>
        <div className="text-sm space-y-1">
          <p className="font-bold text-gray-900 border-b pb-1">
            {hotspot.is_live_firms ? 'NASA FIRMS Detection' : 'Thermal Hotspot'}
          </p>
          <p><strong>Satellite:</strong> {hotspot.satellite || 'VIIRS'} ({hotspot.source})</p>
          <p><strong>FRP:</strong> {frpDisplay}</p>
          <p><strong>Confidence:</strong> {confLabel}</p>
          <p><strong>Acquired (UTC):</strong> {new Date(hotspot.acquired_at).toUTCString()}</p>
          <button 
            className="mt-2 w-full text-xs bg-slate-900 hover:bg-slate-800 text-white font-medium px-2 py-1.5 rounded transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              onClick(hotspot);
            }}
          >
            View Observation Details
          </button>
        </div>
      </Popup>
    </Marker>
  );
}
