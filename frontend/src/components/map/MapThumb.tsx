import React from 'react';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import L from 'leaflet';

// Fix leaflet icon issue in react
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapThumbProps {
  lat: number;
  lng: number;
}

export const MapThumb: React.FC<MapThumbProps> = ({ lat, lng }) => {
  return (
    <div className="h-16 w-16 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-inner z-0 pointer-events-none relative">
      <MapContainer 
        center={[lat, lng]} 
        zoom={14} 
        zoomControl={false} 
        attributionControl={false}
        className="h-full w-full"
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png"
        />
        <Marker position={[lat, lng]} />
      </MapContainer>
      <div className="absolute inset-0 bg-gradient-to-t from-slate-900/20 to-transparent z-[400]" />
    </div>
  );
};
