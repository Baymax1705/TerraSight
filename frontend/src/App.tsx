import { Search, MapPin, Building, ShieldAlert, Loader2, Navigation } from 'lucide-react';
import { useState } from 'react';
import Map from './components/Map';

export default function App() {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [mapCenter, setMapCenter] = useState<[number, number]>([26.8467, 80.9462]); // Default: Lucknow

    // Real Estate Data State
    const [insights, setInsights] = useState<any>(null);
    const [facilities, setFacilities] = useState<any>(null);
    const [isLoadingInsights, setIsLoadingInsights] = useState(false);

    const handleSearch = async () => {
        if (!searchQuery) return;
        setIsSearching(true);
        try {
            const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery + ', Uttar Pradesh, India')}&format=json&limit=5`);
            const data = await res.json();
            setSearchResults(data);
        } catch (err) {
            console.error('Error fetching generic location:', err);
        }
        setIsSearching(false);
    };

    const handleSelectLocation = async (lat: string, lon: string, displayName: string) => {
        setMapCenter([parseFloat(lat), parseFloat(lon)]);
        setSearchQuery(displayName);
        setSearchResults([]);
        
        setIsLoadingInsights(true);
        try {
            // Fetch Circle Rates (FastAPI)
            const rateRes = await fetch(`http://localhost:8000/api/circle-rates?query=${encodeURIComponent(displayName)}`);
            if (rateRes.ok) setInsights(await rateRes.json());

            // Fetch Facilities (FastAPI)
            const facRes = await fetch(`http://localhost:8000/api/facilities?lat=${lat}&lon=${lon}&radius_m=2000`);
            if (facRes.ok) setFacilities(await facRes.json());
        } catch (err) {
            console.error("Backend connection failed. Make sure FastAPI is running on port 8000.", err);
        }
        setIsLoadingInsights(false);
    };

    return (
        <main className="flex h-screen w-full bg-slate-50 text-slate-900 overflow-hidden font-sans">
            {/* Sidebar */}
            <aside className="w-[420px] bg-white shadow-xl z-20 flex flex-col h-full border-r border-slate-200 hide-scrollbar overflow-y-auto relative dropdown-container">
                <div className="p-6 bg-gradient-to-br from-indigo-900 to-indigo-700 text-white shadow-md flex-shrink-0">
                    <h1 className="text-2xl font-bold tracking-tight">GeoIntel<span className="text-indigo-300">UP</span></h1>
                    <p className="text-sm text-indigo-200 mt-1">Smart Land Intelligence Platform (React)</p>
                </div>

                <div className="p-6 flex-1 flex flex-col gap-6 relative">
                    {/* Search Section */}
                    <div className="space-y-3">
                        <label className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Location Search (UP)</label>
                        <div className="relative">
                            <input 
                                type="text" 
                                className="w-full pl-10 pr-24 py-3 bg-slate-100 border-none rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all placeholder:text-slate-400 text-slate-700 font-medium"
                                placeholder="Gomti Nagar, Lucknow..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                            />
                            <Search className="absolute left-3 top-3.5 h-5 w-5 text-slate-400" />
                            <button 
                                onClick={handleSearch}
                                disabled={isSearching}
                                className="absolute right-1 top-1 bottom-1 bg-indigo-600 hover:bg-indigo-700 text-white px-3 rounded-lg font-medium transition-colors text-sm flex items-center justify-center disabled:opacity-70"
                            >
                                {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Find'}
                            </button>
                        </div>

                        {/* Search Results Dropdown */}
                        {searchResults.length > 0 && (
                            <div className="absolute top-20 left-0 right-0 bg-white rounded-xl shadow-2xl border border-slate-100 overflow-hidden z-30 max-h-60 overflow-y-auto mt-2 mx-6">
                                {searchResults.map((result, idx) => (
                                    <div 
                                        key={idx} 
                                        onClick={() => handleSelectLocation(result.lat, result.lon, result.display_name)}
                                        className="p-3 border-b border-slate-50 last:border-0 hover:bg-slate-50 cursor-pointer flex gap-3 items-start transition-colors"
                                    >
                                        <Navigation className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                                        <div className="flex flex-col">
                                            <span className="text-sm font-medium text-slate-800 line-clamp-1">{result.display_name.split(',')[0]}</span>
                                            <span className="text-xs text-slate-500 line-clamp-1">{result.display_name}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                        
                        <button 
                            className="w-full bg-slate-900 hover:bg-slate-800 text-white py-3 rounded-xl font-medium transition-colors shadow-sm active:scale-95 mt-4"
                            onClick={() => {if(searchQuery) handleSelectLocation(mapCenter[0].toString(), mapCenter[1].toString(), searchQuery);}}
                        >
                            Run Smart Analytics
                        </button>
                    </div>

                    <div className="h-px bg-slate-200 w-full rounded-full mt-2"></div>

                    {/* Regional Insights */}
                    <div className="space-y-4">
                        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Quick Insights</h2>
                        
                        {isLoadingInsights ? (
                            <div className="bg-slate-50 border border-slate-100 rounded-xl p-8 flex flex-col items-center justify-center shadow-sm">
                                <Loader2 className="h-8 w-8 text-indigo-500 animate-spin mb-4" />
                                <p className="text-sm font-medium text-slate-600">Scanning local intelligence...</p>
                                <p className="text-xs text-slate-400 mt-1">Cross-referencing IGRS UP values</p>
                            </div>
                        ) : (
                            <>
                                <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex gap-4 items-start shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="bg-emerald-100 text-emerald-600 p-2 rounded-lg mt-0.5">
                                        <Building size={20} />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex justify-between items-center w-full">
                                            <h3 className="font-semibold text-slate-800">Circle Rate Profile</h3>
                                            {insights && <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${['High', 'Very High'].includes(insights.growth_potential) ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>{insights.growth_potential} GROWTH</span>}
                                        </div>
                                        <p className="text-sm text-slate-500 mt-1">
                                            {insights ? <span className="font-semibold text-slate-700">₹{insights.estimated_rate_sqm.toLocaleString()}/sq.m.<br/><span className="font-normal text-xs text-slate-500 mt-2 block border-t pt-2 border-slate-200">{insights.smart_insight}</span></span> : 'Pending scan for target area...'}
                                        </p>
                                    </div>
                                </div>

                                <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex gap-4 items-start shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="bg-blue-100 text-blue-600 p-2 rounded-lg mt-0.5">
                                        <MapPin size={20} />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-slate-800">Nearby Facilities (2km radius)</h3>
                                        <p className="text-sm text-slate-500 mt-1 flex flex-col gap-1">
                                            {facilities ? (
                                                <>
                                                    <span>🏫 {facilities.schools} Schools</span>
                                                    <span>🏥 {facilities.hospitals} Hospitals</span>
                                                    <span>🛒 {facilities.markets} Markets</span>
                                                    <span>🚇 {facilities.transport} Transit Stops</span>
                                                </>
                                            ) : 'Pending scan...'}
                                        </p>
                                    </div>
                                </div>

                                <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex gap-4 items-start shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="bg-rose-100 text-rose-600 p-2 rounded-lg mt-0.5">
                                        <ShieldAlert size={20} />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-slate-800">Risk Assessment</h3>
                                        <p className="text-sm text-slate-500 mt-1">
                                            {insights ? insights.risk_factors : 'Pending hazard evaluation...'}
                                        </p>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </aside>

            {/* Map Area */}
            <section className="flex-1 h-full relative z-0 bg-slate-200">
                <Map center={mapCenter} zoom={14} />
            </section>
        </main>
    );
}
