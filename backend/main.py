import requests
from fastapi import FastAPI, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import datetime
from database import get_db, CachedRate
from scraper import scrape_real_estate_data

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
      node["amenity"="college"](around:{radius_m},{lat},{lon});
      node["amenity"="hospital"](around:{radius_m},{lat},{lon});
      node["amenity"="clinic"](around:{radius_m},{lat},{lon});
      node["amenity"="marketplace"](around:{radius_m},{lat},{lon});
      node["shop"="supermarket"](around:{radius_m},{lat},{lon});
      node["shop"="mall"](around:{radius_m},{lat},{lon});
      node["public_transport"="station"](around:{radius_m},{lat},{lon});
      node["highway"="bus_stop"](around:{radius_m},{lat},{lon});
      node["leisure"="fitness_centre"](around:{radius_m},{lat},{lon});
      node["leisure"="park"](around:{radius_m},{lat},{lon});
      node["amenity"="police"](around:{radius_m},{lat},{lon});
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
    
    # Initialize categories
    categories = {
        "Schools & Colleges": [],
        "Hospitals & Clinics": [],
        "Marts & Markets": [],
        "Public Transport": [],
        "Gyms & Fitness": [],
        "Parks": [],
        "Police Stations": []
    }
    locations = []
    
    for element in data.get("elements", []):
        if element.get("type") == "node" and "tags" in element:
            tags = element["tags"]
            name = tags.get("name", "Unknown Facility")
            if name == "Unknown Facility": continue # Skip nameless things to avoid cluttering lists
            
            amenity = tags.get("amenity", "")
            shop = tags.get("shop", "")
            transport = tags.get("public_transport", "")
            highway = tags.get("highway", "")
            leisure = tags.get("leisure", "")
            
            type_lbl = None
            category = None
            
            if amenity in ["school", "college", "university"]:
                category = "Schools & Colleges"
                type_lbl = "Education"
            elif amenity in ["hospital", "clinic", "pharmacy"]:
                category = "Hospitals & Clinics"
                type_lbl = "Medical"
            elif amenity == "marketplace" or shop in ["supermarket", "convenience", "mall"]:
                category = "Marts & Markets"
                type_lbl = "Market"
            elif transport == "station" or highway == "bus_stop":
                category = "Public Transport"
                type_lbl = "Transit Station"
            elif leisure in ["fitness_centre", "sports_centre"]:
                category = "Gyms & Fitness"
                type_lbl = "Gym"
            elif leisure == "park":
                category = "Parks"
                type_lbl = "Park"
            elif amenity == "police":
                category = "Police Stations"
                type_lbl = "Police"
                
            if category and type_lbl:
                fac_obj = {
                    "name": name,
                    "type": type_lbl,
                    "lat": element.get("lat"),
                    "lon": element.get("lon")
                }
                categories[category].append(fac_obj)
                locations.append(fac_obj)
                
    return {
        "categories": categories,
        "locations": locations,
        "total_facilities": len(locations),
        "radius": radius_m
    }

@app.get("/api/circle-rates")
def get_circle_rates(
    query: str = Query(..., description="Location query to match UP district"),
    db: Session = Depends(get_db)
):
    query_lower = query.lower().strip()
    
    # 1. Check Database Cache First
    cached_entry = db.query(CachedRate).filter(CachedRate.location_query == query_lower).first()
    
    if cached_entry:
        # Check if data is fresher than 30 days
        age_in_days = (datetime.datetime.utcnow() - cached_entry.updated_at).days
        if age_in_days < 30:
            return {
                "location": query.title(),
                "estimated_rate_sqm": cached_entry.estimated_rate_sqm,
                "growth_potential": cached_entry.growth_potential,
                "risk_factors": cached_entry.risk_factors,
                "smart_insight": cached_entry.smart_insight,
                "source": "Database Cache (0 latency)"
            }

    # 2. Scrape Live Data (or fallback heuristic)
    scraped_data = scrape_real_estate_data(query)
    
    # 3. Store / Update the Database
    if cached_entry:
        cached_entry.estimated_rate_sqm = scraped_data["estimated_rate_sqm"]
        cached_entry.growth_potential = scraped_data["growth_potential"]
        cached_entry.risk_factors = scraped_data["risk_factors"]
        cached_entry.smart_insight = scraped_data["smart_insight"]
        cached_entry.source = scraped_data["source"]
        cached_entry.updated_at = datetime.datetime.utcnow()
    else:
        new_entry = CachedRate(
            location_query=query_lower,
            estimated_rate_sqm=scraped_data["estimated_rate_sqm"],
            growth_potential=scraped_data["growth_potential"],
            risk_factors=scraped_data["risk_factors"],
            smart_insight=scraped_data["smart_insight"],
            source=scraped_data["source"]
        )
        db.add(new_entry)
        
    db.commit()
    
    return {
        "location": query.title(),
        "estimated_rate_sqm": scraped_data["estimated_rate_sqm"],
        "growth_potential": scraped_data["growth_potential"],
        "risk_factors": scraped_data["risk_factors"],
        "smart_insight": scraped_data["smart_insight"],
        "source": scraped_data["source"]
    }
