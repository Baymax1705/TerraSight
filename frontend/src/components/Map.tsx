import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

function ChangeView({ center, zoom }: { center: [number, number], zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, zoom, { duration: 1.5 });
  }, [center, zoom, map]);
  return null;
}

function ClickHandler({ onClick }: { onClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export default function Map({ 
    center = [26.8467, 80.9462], 
    zoom = 15,
    onMapClick,
    facilities = []
}: { 
    center: [number, number]; 
    zoom?: number;
    onMapClick?: (lat: number, lng: number) => void;
    facilities?: any[];
}) {
    useEffect(() => {
        // Fix Leaflet base icons issue
        delete (L.Icon.Default.prototype as any)._getIconUrl;
        L.Icon.Default.mergeOptions({
            iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
            iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
            shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        });
    }, []);

    // Helper for custom colored icons
    const createFacilityIcon = (type: string) => {
        let color = '#3b82f6'; // default blue
        let emoji = '📍';
        if (type === 'Education') { color = '#eab308'; emoji = '🏫'; }
        else if (type === 'Medical') { color = '#ef4444'; emoji = '🏥'; }
        else if (type === 'Market') { color = '#10b981'; emoji = '🛒'; }
        else if (type === 'Transit Station') { color = '#8b5cf6'; emoji = '🚇'; }
        else if (type === 'Gym') { color = '#f97316'; emoji = '🏋️'; }
        else if (type === 'Park') { color = '#22c55e'; emoji = '🌳'; }
        else if (type === 'Police') { color = '#0ea5e9'; emoji = '🚓'; }

        return L.divIcon({
            className: 'custom-facility-icon',
            html: `<div style="background-color: ${color}; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); font-size: 14px;">${emoji}</div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });
    };

    return (
        <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%', zIndex: 0 }}>
            <ChangeView center={center} zoom={zoom} />
            {onMapClick && <ClickHandler onClick={onMapClick} />}
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {/* Target Pin */}
            <Marker position={center}>
                <Popup>
                    <strong>Analysis Target</strong><br/>
                    Lat: {center[0].toFixed(4)}<br/>
                    Lng: {center[1].toFixed(4)}
                </Popup>
            </Marker>

            {/* Facility Pins */}
            {facilities.map((fac, idx) => (
                <Marker key={idx} position={[fac.lat, fac.lon]} icon={createFacilityIcon(fac.type)}>
                    <Popup>
                        <strong>{fac.name}</strong><br/>
                        <span style={{ fontSize: '12px', color: '#666' }}>{fac.type}</span>
                    </Popup>
                </Marker>
            ))}
        </MapContainer>
    );
}
