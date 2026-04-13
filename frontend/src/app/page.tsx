'use client';
import dynamic from 'next/dynamic';
import { Search, MapPin, Building, ShieldAlert, AlignLeft } from 'lucide-react';
import { useState } from 'react';

// Dynamically load the Map component to avoid SSR window errors with Leaflet
const Map = dynamic(() => import('../components/Map'), { ssr: false, loading: () => <div className="h-full w-full bg-slate-100 animate-pulse flex items-center justify-center text-slate-500">Loading Map...</div> });

export default function Home() {
    const [searchQuery, setSearchQuery] = useState('');

    return (
        <main className="flex h-screen w-full bg-slate-50 text-slate-900 overflow-hidden font-sans">
            {/* Sidebar */}
            <aside className="w-96 bg-white shadow-xl z-10 flex flex-col h-full border-r border-slate-200 hide-scrollbar overflow-y-auto relative">
                <div className="p-6 bg-gradient-to-br from-indigo-900 to-indigo-700 text-white shadow-md">
                    <h1 className="text-2xl font-bold tracking-tight">GeoIntel<span className="text-indigo-300">UP</span></h1>
                    <p className="text-sm text-indigo-200 mt-1">Smart Land Intelligence Platform</p>
                </div>

                <div className="p-6 flex-1 flex flex-col gap-6">
                    {/* Search Section */}
                    <div className="space-y-3">
                        <label className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Location Search</label>
                        <div className="relative">
                            <input 
                                type="text" 
                                className="w-full pl-10 pr-4 py-3 bg-slate-100 border-none rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all placeholder:text-slate-400 text-slate-700 font-medium"
                                placeholder="e.g. Gomti Nagar, Lucknow..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                            <Search className="absolute left-3 top-3.5 h-5 w-5 text-slate-500" />
                        </div>
                        <button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-xl font-medium transition-colors shadow-sm active:scale-95">
                            Analyze Region
                        </button>
                    </div>

                    <div className="h-px bg-slate-200 w-full rounded-full"></div>

                    {/* Regional Insights (Placeholder for actual data) */}
                    <div className="space-y-4">
                        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Quick Insights</h2>
                        
                        <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex gap-4 items-start shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                            <div className="bg-emerald-100 text-emerald-600 p-2 rounded-lg mt-0.5">
                                <Building size={20} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-800">Circle Rate Range</h3>
                                <p className="text-sm text-slate-500 mt-1">Data not loaded. Enter a region to fetch UP govt rates.</p>
                            </div>
                        </div>

                        <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex gap-4 items-start shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                            <div className="bg-blue-100 text-blue-600 p-2 rounded-lg mt-0.5">
                                <MapPin size={20} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-800">Nearby Facilities</h3>
                                <p className="text-sm text-slate-500 mt-1">Schools, hospitals, and transit hubs within 2km.</p>
                            </div>
                        </div>

                        <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex gap-4 items-start shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                            <div className="bg-rose-100 text-rose-600 p-2 rounded-lg mt-0.5">
                                <ShieldAlert size={20} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-800">Risk Assessment</h3>
                                <p className="text-sm text-slate-500 mt-1">Flood zones and industrial proximities.</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className="p-4 border-t border-slate-100 bg-slate-50 text-xs text-center text-slate-500">
                    Uttar Pradesh Geospatial Intelligence &copy; 2026
                </div>
            </aside>

            {/* Map Area */}
            <section className="flex-1 h-full relative">
                <Map />
                
                {/* Floating Map Actions */}
                <div className="absolute top-6 right-6 z-10 flex flex-col gap-2">
                     <button className="bg-white/90 backdrop-blur-md p-3 rounded-full shadow-lg text-slate-700 hover:text-indigo-600 transition-colors border border-slate-200">
                        <AlignLeft size={20} />
                     </button>
                </div>
            </section>
        </main>
    );
}
