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
