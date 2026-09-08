"use client";

import { Marker, Popup, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import { Hotspot, PersistenceProfileResponse } from '../services/api';

// Create a custom icon for hotspots with Phase 3 persistence intelligence
const createHotspotIcon = (confidence: string, persistenceClass?: string) => {
  const conf = confidence.toLowerCase();
  const baseColor = (conf === 'high' || conf === 'h') ? '#ef4444' : (conf === 'nominal' || conf === 'n') ? '#f97316' : '#eab308';
  
  if (persistenceClass === 'PERSISTENT') {
    // Persistent: Orange thermal core + clearly visible glowing purple outer ring / halo
    return L.divIcon({
      className: 'custom-div-icon',
      html: `
        <div style="position:relative; width:26px; height:26px; display:flex; align-items:center; justify-content:center;">
          <div style="position:absolute; inset:0; border-radius:50%; border:2.5px solid #a855f7; background:rgba(168,85,247,0.25); box-shadow:0 0 10px rgba(168,85,247,0.75);"></div>
          <div style="position:relative; width:12px; height:12px; border-radius:50%; background:${baseColor}; border:2px solid #ffffff; box-shadow:0 0 4px rgba(0,0,0,0.6);"></div>
        </div>
      `,
      iconSize: [26, 26],
      iconAnchor: [13, 13]
    });
  }

  if (persistenceClass === 'RECURRING') {
    // Recurring: Orange thermal core + subtler dashed purple ring
    return L.divIcon({
      className: 'custom-div-icon',
      html: `
        <div style="position:relative; width:22px; height:22px; display:flex; align-items:center; justify-content:center;">
          <div style="position:absolute; inset:0; border-radius:50%; border:2px dashed #c084fc; background:rgba(192,132,252,0.15);"></div>
          <div style="position:relative; width:12px; height:12px; border-radius:50%; background:${baseColor}; border:1.5px solid #ffffff;"></div>
        </div>
      `,
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });
  }

  if (persistenceClass === 'INSUFFICIENT_HISTORY') {
    // Insufficient history: subtle neutral border
    return L.divIcon({
      className: 'custom-div-icon',
      html: `<div style="background-color:${baseColor}; width:16px; height:16px; border-radius:50%; border:2px solid #94a3b8; box-shadow: 0 0 4px rgba(0,0,0,0.4);"></div>`,
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    });
  }

  // Standard FIRMS thermal detection (ISOLATED / OCCASIONAL / default)
  return L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="background-color:${baseColor}; width:16px; height:16px; border-radius:50%; border:2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.6);"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });
};

interface HotspotMarkerProps {
  hotspot: Hotspot;
  profile?: PersistenceProfileResponse | null;
  onClick: (hotspot: Hotspot) => void;
}

export function HotspotMarker({ hotspot, profile, onClick }: HotspotMarkerProps) {
  const conf = hotspot.confidence.toLowerCase();
  const confLabel = conf === 'h' ? 'High' : conf === 'n' ? 'Nominal' : conf === 'l' ? 'Low' : hotspot.confidence;
  const frpDisplay = hotspot.frp_mw != null ? `${hotspot.frp_mw} MW` : 'N/A';

  return (
    <Marker 
      position={[hotspot.latitude, hotspot.longitude]} 
      icon={createHotspotIcon(hotspot.confidence, profile?.persistence_class)}
      eventHandlers={{
        click: () => onClick(hotspot)
      }}
    >
      <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
        <div className="text-xs font-sans leading-tight py-0.5 px-1 min-w-[150px]">
          <div className="font-bold text-slate-900">{hotspot.is_live_firms ? 'NASA FIRMS Detection' : 'Thermal Hotspot'}</div>
          <div className="text-slate-600 text-[11px]">{hotspot.satellite || 'VIIRS'} / {hotspot.instrument || 'VIIRS'}</div>
          <div className="text-slate-700 font-medium text-[11px]">FRP: {frpDisplay}</div>
          {profile && (
            <div className="mt-1.5 pt-1.5 border-t border-slate-200">
              <div className="font-semibold text-purple-700 text-[11px] flex items-center gap-1">
                <span>Temporal:</span> {profile.persistence_class.replace('_', ' ')}
              </div>
              <div className="text-slate-600 text-[10px]">
                Persistence Index: {profile.persistence_index} / 100
              </div>
            </div>
          )}
        </div>
      </Tooltip>
      <Popup>
        <div className="text-sm space-y-1">
          <p className="font-bold text-gray-900 border-b pb-1">
            {hotspot.is_live_firms ? 'NASA FIRMS Detection' : 'Thermal Hotspot'}
          </p>
          <p><strong>Satellite:</strong> {hotspot.satellite || 'VIIRS'} ({hotspot.source})</p>
          <p><strong>FRP:</strong> {frpDisplay}</p>
          <p><strong>Confidence:</strong> {confLabel}</p>
          <p><strong>Acquired (UTC):</strong> {new Date(hotspot.acquired_at).toUTCString()}</p>
          {profile && (
            <div className="mt-2 pt-2 border-t border-slate-200 text-xs">
              <p className="text-purple-700 font-bold">
                Temporal: {profile.persistence_class.replace('_', ' ')} ({profile.persistence_index}/100)
              </p>
              <p className="text-slate-600 text-[11px]">
                Active Days (30d): {profile.active_days_30d} &bull; Weeks: {profile.active_weeks_30d}
              </p>
            </div>
          )}
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
