import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Smart Land Intelligence API",
    description="Backend for querying real estate data, circle rates, and nearby facilities.",
    version="0.1.0"
)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Land Intelligence API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/facilities")
def get_nearby_facilities(lat: float = Query(...), lon: float = Query(...), radius_m: int = 2000):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="school"](around:{radius_m},{lat},{lon});
      node["amenity"="hospital"](around:{radius_m},{lat},{lon});
      node["amenity"="marketplace"](around:{radius_m},{lat},{lon});
      node["public_transport"="station"](around:{radius_m},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """
    try:
        response = requests.post(overpass_url, data={'data': overpass_query}, timeout=10)
    except requests.RequestException as e:
         return {"error": "Failed to connect to Overpass API", "details": str(e)}

    if response.status_code != 200:
        return {"error": "Overpass query failed", "details": response.text}
        
    data = response.json()
    facilities = {"schools": 0, "hospitals": 0, "markets": 0, "transport": 0, "locations": [], "radius": radius_m}
    
    for element in data.get("elements", []):
        if element.get("type") == "node" and "tags" in element:
            tags = element["tags"]
            amenity_type = tags.get("amenity")
            transport_type = tags.get("public_transport")
            name = tags.get("name", "Unknown")
            
            if amenity_type == "school":
                facilities["schools"] += 1
                type_lbl = "School"
            elif amenity_type == "hospital":
                facilities["hospitals"] += 1
                type_lbl = "Hospital"
            elif amenity_type == "marketplace":
                facilities["markets"] += 1
                type_lbl = "Market"
            elif transport_type == "station":
                facilities["transport"] += 1
                type_lbl = "Transit Station"
            else:
                continue
                
            facilities["locations"].append({
                "name": name,
                "type": type_lbl,
                "lat": element.get("lat"),
                "lon": element.get("lon")
            })
            
    return facilities

import random

UP_DISTRICTS = {
    "lucknow": {"base_rate": 4500, "multiplier": 1.2, "growth": "High", "risk": "Moderate flood risk near Gomti river."},
    "noida": {"base_rate": 8500, "multiplier": 1.5, "growth": "Very High", "risk": "Industrial zoning restrictions in some sectors."},
    "kanpur": {"base_rate": 3500, "multiplier": 1.0, "growth": "Medium", "risk": "High pollution zone, leather tanning cluster."},
    "varanasi": {"base_rate": 6000, "multiplier": 1.3, "growth": "High", "risk": "Heritage restriction zones."},
    "agra": {"base_rate": 4000, "multiplier": 0.9, "growth": "Low", "risk": "Taj Trapezium Zone extreme restrictions."},
}

@app.get("/api/circle-rates")
def get_circle_rates(query: str = Query(..., description="Location query to match UP district")):
    query_lower = query.lower()
    
    matched_district = None
    for district in UP_DISTRICTS.keys():
        if district in query_lower:
            matched_district = district
            break
            
    if not matched_district:
        # Default fallback
        data = {"base_rate": random.randint(2000, 4000), "multiplier": 1.0, "growth": "Moderate", "risk": "Standard assessment. General agricultural / semi-urban."}
    else:
        data = UP_DISTRICTS[matched_district]
        
    variance = random.randint(-500, 500)
    current_rate = data["base_rate"] * data["multiplier"] + variance
    
    # Generate Smart Insight
    if data["growth"] in ["High", "Very High"]:
        insight = f"This area shows strong investment potential. Government circle rates are averaging around ₹{int(current_rate)}/sq.m. Expected appreciation is robust."
    else:
        insight = f"Steady market. Current valuations hover around ₹{int(current_rate)}/sq.m. Caution advised regarding {data['risk'].lower()}"
        
    return {
        "location": query.title(),
        "estimated_rate_sqm": int(current_rate),
        "growth_potential": data["growth"],
        "risk_factors": data["risk"],
        "smart_insight": insight,
        "source": "UP IGRS Valuation (MVP Heuristic)"
    }
