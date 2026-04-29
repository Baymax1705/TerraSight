import { Search, MapPin, Building, ShieldAlert, Loader2, Navigation, Target, TrendingUp, HandCoins } from 'lucide-react';
import { useState, useMemo } from 'react';
import Map from './components/Map';

export default function App() {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [targetLocation, setTargetLocation] = useState<[number, number]>([26.8467, 80.9462]); 
    const [mapView, setMapView] = useState<[number, number]>([26.8467, 80.9462]); 
    const [selectedFacility, setSelectedFacility] = useState<any>(null);
    const [activeCategoryFilter, setActiveCategoryFilter] = useState<string | null>(null);
    const [landArea, setLandArea] = useState<number>(1000); // Default 1000
    const [areaUnit, setAreaUnit] = useState<'sq.ft' | 'sq.m' | 'sq.yd'>('sq.ft');

    // Data State
    const [insights, setInsights] = useState<any>(null);
    const [facilities, setFacilities] = useState<any>(null);
    const [isLoadingInsights, setIsLoadingInsights] = useState(false);

    // Dynamic bounded search for UP
    const handleSearch = async () => {
        if (!searchQuery) return;
        setIsSearching(true);
        try {
            const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery + ', Uttar Pradesh, India')}&format=json&limit=5`);
            const data = await res.json();
            setSearchResults(data);
        } catch (err) {
            console.error('Error fetching location:', err);
        }
        setIsSearching(false);
    };

    const handleSelectLocation = async (lat: string, lon: string, displayName: string) => {
        const newLoc: [number, number] = [parseFloat(lat), parseFloat(lon)];
        setTargetLocation(newLoc);
        setMapView(newLoc);
        setSelectedFacility(null);
        setActiveCategoryFilter(null);
        setSearchQuery(displayName);
        setSearchResults([]);
        // Analytics run paused until button is explicitly clicked
    };

    const handleMapClick = async (lat: number, lng: number) => {
        const newLoc: [number, number] = [lat, lng];
        setTargetLocation(newLoc);
        setMapView(newLoc);
        setSelectedFacility(null);
        setActiveCategoryFilter(null);
        
        // Reverse Geocode to update text only
        try {
            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`);
            const data = await res.json();
            const placeName = data.display_name || `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            setSearchQuery(placeName); // Use the Full Address!
        } catch(e) {
            console.error("Reverse geocode failed", e);
            setSearchQuery(`${lat.toFixed(4)}, ${lng.toFixed(4)}`);
        }
    };

    const triggerAnalytics = async () => {
        setIsLoadingInsights(true);
        try {
            const rateRes = await fetch(`http://localhost:8000/api/circle-rates?query=${encodeURIComponent(searchQuery)}`);
            if (rateRes.ok) setInsights(await rateRes.json());

            const facRes = await fetch(`http://localhost:8000/api/facilities?lat=${targetLocation[0]}&lon=${targetLocation[1]}&radius_m=2000`);
            if (facRes.ok) setFacilities(await facRes.json());
        } catch (err) {
            console.error("Backend connection failed.", err);
        }
        setIsLoadingInsights(false);
    };

    // Calculate Valuations based on Area and Facilities
    const valuations = useMemo(() => {
        if (!insights) return null;
        
        // Convert Area to Sq Meters for valuation math
        let areaInSqM = landArea;
        if (areaUnit === 'sq.ft') areaInSqM = landArea / 10.764;
        else if (areaUnit === 'sq.yd') areaInSqM = landArea / 1.196;

        const govtRateTotal = insights.estimated_rate_sqm * areaInSqM;
        
        // Compute Premium based on Facilities
        let premiumPercent = 0;
        if (facilities && facilities.total_facilities) {
            const totalFacs = facilities.total_facilities;
            if (totalFacs > 30) premiumPercent = 35;
            else if (totalFacs > 15) premiumPercent = 20;
            else if (totalFacs > 5) premiumPercent = 10;
        }
        
        const marketRateSqm = insights.estimated_rate_sqm * (1 + premiumPercent / 100);
        const marketRateTotal = marketRateSqm * areaInSqM;

        return {
            govtRateTotal,
            marketRateSqm,
            marketRateTotal,
            premiumPercent
        };
    }, [insights, facilities, landArea, areaUnit]);

    const filteredFacilitiesForMap = useMemo(() => {
        if (!facilities) return [];
        if (!activeCategoryFilter) return facilities.locations;
        return facilities.categories[activeCategoryFilter] || [];
    }, [facilities, activeCategoryFilter]);

    return (
        <main className="flex h-screen w-full bg-slate-50 text-slate-900 overflow-hidden font-sans">
            {/* Sidebar */}
            <aside className="w-[450px] bg-white shadow-xl z-20 flex flex-col h-full border-r border-slate-200 hide-scrollbar overflow-y-auto relative dropdown-container">
                <div className="p-6 bg-gradient-to-br from-indigo-900 to-indigo-700 text-white shadow-md flex-shrink-0">
                    <h1 className="text-2xl font-bold tracking-tight">GeoIntel<span className="text-indigo-300">UP</span></h1>
                    <p className="text-sm text-indigo-200 mt-1">Dual-Valuation Smart Engine</p>
                </div>

                <div className="p-6 flex-1 flex flex-col gap-6 relative">
                    {/* Search Section */}
                    <div className="space-y-3">
                        <label className="text-sm font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-2"><Target size={16}/> Target Area</label>
                        <div className="relative">
                            <input 
                                type="text" 
                                className="w-full pl-10 pr-24 py-3 bg-slate-100 border-none rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all placeholder:text-slate-400 text-slate-700 font-medium text-sm"
                                placeholder="Search or Click on Map..."
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
                                {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search'}
                            </button>
                        </div>

                        {searchResults.length > 0 && (
                            <div className="absolute top-20 left-0 right-0 bg-white rounded-xl shadow-2xl border border-slate-100 overflow-hidden z-30 max-h-60 overflow-y-auto mt-2 mx-6">
                                {searchResults.map((result, idx) => (
                                    <div 
                                        key={idx} 
                                        onClick={() => handleSelectLocation(result.lat, result.lon, result.display_name)}
                                        className="p-3 border-b border-slate-50 last:border-0 hover:bg-slate-50 cursor-pointer flex gap-3 items-start transition-colors"
                                    >
                                        <Navigation className="h-4 w-4 text-indigo-400 mt-0.5 flex-shrink-0" />
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
                            onClick={triggerAnalytics}
                        >
                            Run Smart Analytics
                        </button>
                    </div>

                    {/* Dimensions Input */}
                    <div className="space-y-3 bg-indigo-50/50 p-4 rounded-xl border border-indigo-100">
                        <div className="flex justify-between items-center mb-2">
                            <label className="text-sm font-semibold text-slate-700">Land Area Dimension</label>
                            
                            {/* Unit Options Toggle */}
                            <div className="flex bg-white rounded-md border border-indigo-200 shadow-sm overflow-hidden text-xs font-semibold">
                                <button className={`px-2 py-1 transition-colors ${areaUnit === 'sq.ft' ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:bg-slate-50'}`} onClick={() => setAreaUnit('sq.ft')}>Sq.Ft</button>
                                <button className={`px-2 py-1 transition-colors border-l border-r border-indigo-100 ${areaUnit === 'sq.m' ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:bg-slate-50'}`} onClick={() => setAreaUnit('sq.m')}>Sq.M</button>
                                <button className={`px-2 py-1 transition-colors ${areaUnit === 'sq.yd' ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:bg-slate-50'}`} onClick={() => setAreaUnit('sq.yd')}>Gaj</button>
                            </div>
                        </div>
                        
                        <div className="flex items-center gap-4">
                            <input 
                                type="number" 
                                value={landArea} 
                                onChange={(e) => setLandArea(Number(e.target.value) || 0)}
                                className="w-24 px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm text-sm font-bold text-indigo-700 focus:ring-2 focus:ring-indigo-500 outline-none"
                            />
                            <input 
                                type="range" 
                                min="10" max={areaUnit === 'sq.ft' ? "100000" : "10000"} step={areaUnit === 'sq.ft' ? "100" : "50"}
                                value={landArea}
                                onChange={(e) => setLandArea(parseInt(e.target.value))}
                                className="flex-1 cursor-pointer accent-indigo-600"
                            />
                        </div>
                    </div>

                    <div className="h-px bg-slate-200 w-full rounded-full"></div>

                    {/* Analytics Dashboard */}
                    <div className="space-y-4">
                        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Intelligence Report</h2>
                        
                        {isLoadingInsights ? (
                            <div className="bg-slate-50 border border-slate-100 rounded-xl p-8 flex flex-col items-center justify-center shadow-sm">
                                <Loader2 className="h-8 w-8 text-indigo-500 animate-spin mb-4" />
                                <p className="text-sm font-medium text-slate-600">Generating Valuation Report...</p>
                            </div>
                        ) : !insights ? (
                            <div className="bg-slate-50 border border-slate-100 rounded-xl p-8 text-center text-slate-500 text-sm leading-relaxed">
                                Use the search bar or drop a map pin,<br/>then click <b>Run Smart Analytics</b>!
                            </div>
                        ) : (
                            <div className="flex flex-col gap-4 pb-4">
                                
                                {/* Dual Valuation Engine */}
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col justify-between">
                                        <div className="flex items-center gap-2 mb-2 text-slate-600">
                                            <Building size={16}/> <span className="text-xs font-semibold uppercase">Govt Rate</span>
                                        </div>
                                        <p className="text-lg font-bold text-slate-800">₹{Math.round(valuations?.govtRateTotal || 0).toLocaleString()}</p>
                                        <div className="flex flex-col mt-1">
                                            <p className="text-[10px] text-slate-500">₹{insights.estimated_rate_sqm.toLocaleString()}/sq.m base</p>
                                            <p className="text-[9px] text-slate-400 mt-0.5 truncate" title={insights.source}>Data: {insights.source}</p>
                                        </div>
                                    </div>
                                    <div className="bg-indigo-600 border border-indigo-700 rounded-xl p-4 shadow-md flex flex-col justify-between text-white relative overflow-hidden">
                                        <div className="absolute -right-3 -top-3 opacity-10"><TrendingUp size={64}/></div>
                                        <div className="flex items-center gap-2 mb-2">
                                            <HandCoins size={16}/> <span className="text-xs font-semibold uppercase">Est. Market</span>
                                        </div>
                                        <p className="text-lg font-bold">₹{Math.round(valuations?.marketRateTotal || 0).toLocaleString()}</p>
                                        <p className="text-[10px] text-indigo-200 mt-1">+{valuations?.premiumPercent}% Amenities Premium</p>
                                    </div>
                                </div>

                                {/* Facilities UI */}
                                <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
                                    <div className="flex items-center gap-2 mb-3 border-b border-slate-100 pb-2">
                                        <MapPin size={18} className="text-blue-500"/> 
                                        <h3 className="font-semibold text-sm text-slate-800">Nearby Amenities ({facilities ? facilities.total_facilities : 0})</h3>
                                    </div>
                                    
                                    {/* Category Filter Pills */}
                                    {facilities && facilities.categories && (
                                        <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2 mb-2">
                                            <button 
                                                onClick={() => setActiveCategoryFilter(null)}
                                                className={`whitespace-nowrap px-3 py-1.5 rounded-full text-[11px] font-bold transition-all shadow-sm ${activeCategoryFilter === null ? 'bg-indigo-600 text-white shadow-indigo-200' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                                            >
                                                All
                                            </button>
                                            {Object.entries(facilities.categories).map(([catName, items]: [string, any]) => {
                                                if (items.length === 0) return null;
                                                return (
                                                    <button 
                                                        key={catName}
                                                        onClick={() => setActiveCategoryFilter(catName)}
                                                        className={`whitespace-nowrap px-3 py-1.5 rounded-full text-[11px] font-bold transition-all shadow-sm ${activeCategoryFilter === catName ? 'bg-indigo-600 text-white shadow-indigo-200' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                                                    >
                                                        {catName.split(' & ')[0]} ({items.length})
                                                    </button>
                                                )
                                            })}
                                        </div>
                                    )}

                                    {facilities && facilities.categories ? (
                                        <div className="flex flex-col gap-2">
                                            {Object.entries(facilities.categories).map(([categoryName, items]: [string, any]) => {
                                                if (items.length === 0) return null;
                                                if (activeCategoryFilter && activeCategoryFilter !== categoryName) return null;
                                                const isOpen = activeCategoryFilter === categoryName;
                                                return (
                                                    <details key={categoryName} open={isOpen} className="group bg-slate-50 border border-slate-200 rounded-lg overflow-hidden cursor-pointer">
                                                        <summary className="flex items-center justify-between px-3 py-2 text-xs font-semibold text-slate-700 select-none group-open:bg-indigo-50 hover:bg-slate-100 transition-colors">
                                                            <span>{categoryName}</span>
                                                            <span className="bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">{items.length}</span>
                                                        </summary>
                                                        <div className="px-3 py-2 bg-white text-xs text-slate-600 border-t border-slate-100 max-h-40 overflow-y-auto">
                                                            <ul className="list-none space-y-1">
                                                                {items.map((fac: any, fIdx: number) => {
                                                                    const formattedName = fac.name.replace(/\b\w/g, (c: string) => c.toUpperCase());
                                                                    return (
                                                                        <li 
                                                                            key={fIdx} 
                                                                            onClick={() => {
                                                                                setMapView([fac.lat, fac.lon]);
                                                                                setSelectedFacility(fac);
                                                                            }}
                                                                            className={`line-clamp-1 truncate cursor-pointer p-1.5 rounded-lg transition-all ${selectedFacility?.lat === fac.lat && selectedFacility?.lon === fac.lon ? 'bg-indigo-100 text-indigo-700 font-semibold pl-3 border-l-2 border-indigo-600' : 'hover:bg-slate-50 hover:text-indigo-600'}`}
                                                                            title={formattedName}
                                                                        >
                                                                            • {formattedName}
                                                                        </li>
                                                                    );
                                                                })}
                                                            </ul>
                                                        </div>
                                                    </details>
                                                );
                                            })}
                                        </div>
                                    ) : <p className="text-xs text-slate-500">No data loaded.</p>}
                                </div>

                                {/* Risks UI */}
                                <div className="bg-rose-50 border border-rose-100 rounded-xl p-4 shadow-sm">
                                    <div className="flex items-center gap-2 mb-2">
                                        <ShieldAlert size={18} className="text-rose-500"/> 
                                        <h3 className="font-semibold text-sm text-rose-800">Risk Triggers</h3>
                                    </div>
                                    <p className="text-xs text-rose-600 leading-relaxed font-medium">
                                        {insights.risk_factors}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </aside>

            {/* Map Area */}
            <section className="flex-1 h-full relative z-0 bg-slate-200">
                <Map 
                    targetPin={targetLocation} 
                    mapView={mapView}
                    zoom={15} 
                    onMapClick={handleMapClick}
                    facilities={filteredFacilitiesForMap}
                    selectedFacility={selectedFacility}
                />
            </section>
        </main>
    );
}
