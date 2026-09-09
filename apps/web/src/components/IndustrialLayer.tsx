'use client';

import React from 'react';
import { GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import { OSMFeatureCollection, OSMFeatureGeoJSON } from '../services/api';

interface IndustrialLayerProps {
  data: OSMFeatureCollection | null;
  visible: boolean;
}

export const IndustrialLayer: React.FC<IndustrialLayerProps> = ({ data, visible }) => {
  if (!visible || !data || !data.features || data.features.length === 0) {
    return null;
  }

  const pointToLayer = (feature: OSMFeatureGeoJSON, latlng: L.LatLng) => {
    const category = feature.properties?.feature_category || 'OTHER_INDUSTRIAL';

    let color = '#00bcd4'; // Cyan default
    let radius = 6;

    if (category === 'FLARE') {
      color = '#e91e63'; // Bright Magenta/Pink
      radius = 8;
    } else if (category === 'REFINERY') {
      color = '#9c27b0'; // Deep Purple
      radius = 9;
    } else if (category === 'CHIMNEY') {
      color = '#00e5ff'; // Bright Cyan
      radius = 7;
    } else if (category === 'THERMAL_POWER_PLANT') {
      color = '#ff9800'; // Amber/Orange
      radius = 9;
    } else if (category === 'INDUSTRIAL_AREA') {
      color = '#0288d1'; // Blue
      radius = 5;
    }

    return L.circleMarker(latlng, {
      radius,
      fillColor: color,
      color: '#ffffff',
      weight: 1.5,
      opacity: 0.9,
      fillOpacity: 0.7,
    });
  };

  const style = (feature?: unknown) => {
    const category = (feature as OSMFeatureGeoJSON)?.properties?.feature_category || 'OTHER_INDUSTRIAL';
    let color = '#00bcd4';

    if (category === 'INDUSTRIAL_AREA') {
      color = '#0288d1';
    } else if (category === 'REFINERY') {
      color = '#9c27b0';
    }

    return {
      color,
      weight: 2,
      opacity: 0.8,
      fillColor: color,
      fillOpacity: 0.15,
      dashArray: '4, 4',
    };
  };

  const onEachFeature = (feature: OSMFeatureGeoJSON, layer: L.Layer) => {
    const props = feature.properties;
    const name = props.name || props.osm_uid;
    const category = props.feature_category || 'Industrial Facility';
    const quality = props.geometry_quality;

    const popupContent = `
      <div style="font-family: sans-serif; font-size: 13px; padding: 4px;">
        <div style="font-weight: bold; color: #00bcd4; font-size: 14px; margin-bottom: 4px;">
          🏭 ${name}
        </div>
        <div><strong>Category:</strong> ${category}</div>
        <div><strong>OSM UID:</strong> <code>${props.osm_uid}</code></div>
        <div><strong>Quality:</strong> ${quality}</div>
        <div style="margin-top: 6px; font-size: 11px; color: #888;">
          © OpenStreetMap contributors
        </div>
      </div>
    `;
    layer.bindPopup(popupContent);
  };

  return (
    <GeoJSON
      key={JSON.stringify(data.total_count)}
      data={data as unknown as GeoJSON.FeatureCollection}
      pointToLayer={pointToLayer as unknown as (feature: GeoJSON.Feature, latlng: L.LatLng) => L.Layer}
      style={style}
      onEachFeature={onEachFeature as unknown as (feature: GeoJSON.Feature, layer: L.Layer) => void}
    />
  );
};
