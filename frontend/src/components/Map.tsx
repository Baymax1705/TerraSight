import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Map as MapIcon, Satellite } from 'lucide-react';

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
    targetPin = [26.8467, 80.9462], 
    mapView = [26.8467, 80.9462], 
    zoom = 15,
    onMapClick,
    facilities = [],
    selectedFacility = null
}: { 
    targetPin: [number, number]; 
    mapView: [number, number]; 
    zoom?: number;
    onMapClick?: (lat: number, lng: number) => void;
    facilities?: any[];
    selectedFacility?: any;
}) {
    const [mapType, setMapType] = useState<'street' | 'satellite'>('street');

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
    const createFacilityIcon = (type: string, isSelected: boolean = false) => {
        let color = '#3b82f6'; // default blue
        let emoji = '📍';
        if (type === 'Education') { color = '#eab308'; emoji = '🏫'; }
        else if (type === 'Medical') { color = '#ef4444'; emoji = '🏥'; }
        else if (type === 'Market') { color = '#10b981'; emoji = '🛒'; }
        else if (type === 'Transit Station') { color = '#8b5cf6'; emoji = '🚇'; }
        else if (type === 'Gym') { color = '#f97316'; emoji = '🏋️'; }
        else if (type === 'Park') { color = '#22c55e'; emoji = '🌳'; }
        else if (type === 'Police') { color = '#0ea5e9'; emoji = '🚓'; }

        const dynamicStyle = isSelected 
            ? `box-shadow: 0 0 0 4px rgba(255,255,255,0.9), 0 0 20px ${color}; transform: scale(1.4); z-index: 1000;` 
            : 'box-shadow: 0 2px 5px rgba(0,0,0,0.3); transform: scale(1);';

        return L.divIcon({
            className: 'custom-facility-icon',
            html: `<div style="background-color: ${color}; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; ${dynamicStyle} font-size: 14px; transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);">${emoji}</div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });
    };

    return (
        <div className="relative h-full w-full">
            {/* Custom Premium Map Toggle Overlay */}
            <div className="absolute top-4 right-4 z-[400] bg-white/90 backdrop-blur-md p-1.5 rounded-2xl shadow-xl border border-white/50 flex gap-1">
                <button 
                    onClick={() => setMapType('street')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 ${mapType === 'street' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}
                >
                    <MapIcon size={16} /> Street
                </button>
                <button 
                    onClick={() => setMapType('satellite')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 ${mapType === 'satellite' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}
                >
                    <Satellite size={16} /> Satellite
                </button>
            </div>

            <MapContainer center={mapView} zoom={zoom} style={{ height: '100%', width: '100%', zIndex: 0 }}>
                <ChangeView center={mapView} zoom={zoom} />
                {onMapClick && <ClickHandler onClick={onMapClick} />}
                
                {mapType === 'street' ? (
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                ) : (
                    <TileLayer
                        attribution='Tiles &copy; Esri'
                        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    />
                )}

                {/* Target Pin */}
                <Marker position={targetPin}>
                    <Popup>
                        <strong>Analysis Target</strong><br/>
                        Lat: {targetPin[0].toFixed(4)}<br/>
                        Lng: {targetPin[1].toFixed(4)}
                    </Popup>
                </Marker>

                {/* Facility Pins */}
                {facilities.map((fac, idx) => {
                    const isSelected = selectedFacility && selectedFacility.lat === fac.lat && selectedFacility.lon === fac.lon;
                    return (
                        <Marker 
                            key={idx} 
                            position={[fac.lat, fac.lon]} 
                            icon={createFacilityIcon(fac.type, isSelected)}
                            zIndexOffset={isSelected ? 1000 : 0}
                        >
                            <Popup>
                                <strong>{fac.name}</strong><br/>
                                <span style={{ fontSize: '12px', color: '#666' }}>{fac.type}</span>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>
        </div>
    );
}
