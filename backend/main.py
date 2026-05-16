import os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import datetime
import math
from database import get_db, CachedRate, OfficialCircleRate
from scraper import scrape_real_estate_data
from sentinel import run_sentinel
from ml_multiplier import predict_multiplier

load_dotenv()

app = FastAPI(
    title="Smart Land Intelligence API",
    description="Backend for querying real estate data, circle rates, and nearby facilities.",
    version="0.1.0"
)

# Read allowed origins from env, fallback to allow all for local dev
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000 # radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.get("/api/facilities")
async def get_nearby_facilities(lat: float = Query(...), lon: float = Query(...), radius_m: int = 2000):
    overpass_query = f"""
    [out:json][timeout:25];
    (
      nwr["amenity"="school"](around:{radius_m},{lat},{lon});
      nwr["amenity"="college"](around:{radius_m},{lat},{lon});
      nwr["amenity"="university"](around:{radius_m},{lat},{lon});
      nwr["amenity"="kindergarten"](around:{radius_m},{lat},{lon});
      nwr["amenity"="hospital"](around:{radius_m},{lat},{lon});
      nwr["amenity"="clinic"](around:{radius_m},{lat},{lon});
      nwr["amenity"="doctors"](around:{radius_m},{lat},{lon});
      nwr["amenity"="pharmacy"](around:{radius_m},{lat},{lon});
      nwr["amenity"="marketplace"](around:{radius_m},{lat},{lon});
      nwr["amenity"="police"](around:{radius_m},{lat},{lon});
      nwr["amenity"="bus_station"](around:{radius_m},{lat},{lon});
      nwr["amenity"="gym"](around:{radius_m},{lat},{lon});
      
      nwr["shop"="supermarket"](around:{radius_m},{lat},{lon});
      nwr["shop"="mall"](around:{radius_m},{lat},{lon});
      nwr["shop"="department_store"](around:{radius_m},{lat},{lon});
      nwr["shop"="convenience"](around:{radius_m},{lat},{lon});
      nwr["shop"="clothes"](around:{radius_m},{lat},{lon});
      nwr["shop"="bakery"](around:{radius_m},{lat},{lon});
      
      nwr["public_transport"="station"](around:{radius_m},{lat},{lon});
      nwr["public_transport"="stop_position"](around:{radius_m},{lat},{lon});
      
      nwr["highway"="bus_stop"](around:{radius_m},{lat},{lon});
      
      nwr["railway"="station"](around:{radius_m},{lat},{lon});
      nwr["railway"="subway_entrance"](around:{radius_m},{lat},{lon});
      
      nwr["leisure"="fitness_centre"](around:{radius_m},{lat},{lon});
      nwr["leisure"="sports_centre"](around:{radius_m},{lat},{lon});
      nwr["leisure"="park"](around:{radius_m},{lat},{lon});
      nwr["leisure"="garden"](around:{radius_m},{lat},{lon});
      nwr["leisure"="playground"](around:{radius_m},{lat},{lon});
      
      nwr["sport"="fitness"](around:{radius_m},{lat},{lon});
      nwr["sport"="gymnastics"](around:{radius_m},{lat},{lon});
      nwr["sport"="yoga"](around:{radius_m},{lat},{lon});
      nwr["sport"="weightlifting"](around:{radius_m},{lat},{lon});
      nwr["sport"="bodybuilding"](around:{radius_m},{lat},{lon});
      
      nwr["club"="sport"](around:{radius_m},{lat},{lon});
      nwr["club"="gymnastics"](around:{radius_m},{lat},{lon});
      
      nwr["leisure"="dance"](around:{radius_m},{lat},{lon});
    );
    out center;
    """
    overpass_endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]
    
    headers = {
        'User-Agent': 'TerraSight/1.0 (Contact: local-dev)'
    }
    
    data = None
    last_error = ""
    
    async with httpx.AsyncClient(timeout=12.0) as client:
        for url in overpass_endpoints:
            try:
                response = await client.post(url, data={'data': overpass_query}, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    break
                else:
                    last_error = response.text
            except httpx.RequestError as e:
                 last_error = str(e)
                 continue

    if not data:
        return {"error": "All Overpass API endpoints failed", "details": last_error}
        
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
        if element.get("type") in ["node", "way", "relation"] and "tags" in element:
            tags = element["tags"]
            name = tags.get("name", "Unknown Facility")
            if name == "Unknown Facility": continue # Skip nameless things to avoid cluttering lists
            
            # Extract Lat/Lon handling both Nodes and Ways/Relations (which use "center")
            f_lat = element.get("lat")
            f_lon = element.get("lon")
            if not f_lat or not f_lon:
                center_data = element.get("center")
                if center_data:
                    f_lat = center_data.get("lat")
                    f_lon = center_data.get("lon")
            
            if not f_lat or not f_lon:
                continue
            
            amenity = tags.get("amenity", "")
            shop = tags.get("shop", "")
            transport = tags.get("public_transport", "")
            highway = tags.get("highway", "")
            leisure = tags.get("leisure", "")
            sport = tags.get("sport", "")
            
            type_lbl = None
            category = None
            
            if amenity in ["school", "college", "university", "kindergarten"]:
                category = "Schools & Colleges"
                type_lbl = "Education"
            elif amenity in ["hospital", "clinic", "pharmacy", "doctors"]:
                category = "Hospitals & Clinics"
                type_lbl = "Medical"
            elif amenity == "marketplace" or shop in ["supermarket", "convenience", "mall", "department_store", "clothes", "bakery"]:
                category = "Marts & Markets"
                type_lbl = "Market"
            elif transport in ["station", "stop_position"] or highway == "bus_stop" or tags.get("railway") in ["station", "subway_entrance"] or amenity == "bus_station":
                category = "Public Transport"
                type_lbl = "Transit Station"
            elif leisure in ["fitness_centre", "sports_centre", "dance"] or amenity == "gym" or sport in ["fitness", "gymnastics", "yoga", "weightlifting", "bodybuilding"] or tags.get("club") in ["sport", "gymnastics"]:
                category = "Gyms & Fitness"
                type_lbl = "Gym"
            elif leisure in ["park", "garden", "playground"]:
                category = "Parks"
                type_lbl = "Park"
            elif amenity == "police":
                category = "Police Stations"
                type_lbl = "Police"
                
            if category and type_lbl:
                dist_m = haversine(lat, lon, f_lat, f_lon)
                if dist_m <= radius_m:  # Extra filter to ensure it's strictly within radius
                    fac_obj = {
                        "name": name,
                        "type": type_lbl,
                        "lat": f_lat,
                        "lon": f_lon,
                        "distance_m": round(dist_m)
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
async def get_circle_rates(
    background_tasks: BackgroundTasks,
    query: str = Query(..., description="Location query to match UP district"),
    sentinel: bool = Query(False, description="Whether to trigger the Sentinel autonomous crawler"),
    db: Session = Depends(get_db)
):
    query_lower = query.lower().strip()
    
    if sentinel:
        # Dispatch the Sentinel Protocol to hunt for live data in the background
        background_tasks.add_task(run_sentinel, query)
    query_parts = [p.strip() for p in query_lower.split(",") if len(p.strip()) > 2]
    
    # 0. Check Official ETL Database First (Precision Matching)
    # Intelligently parse the comma-separated address (e.g. "Gomti Nagar, Lucknow, UP")
    # and try to match the most specific geographic identifier first.
    official_match = None
    
    for part in query_parts:
        match = db.query(OfficialCircleRate).filter(
            OfficialCircleRate.locality.ilike(f"%{part}%") |
            OfficialCircleRate.district.ilike(f"%{part}%")
        ).first()
        
        if match:
            official_match = match
            break
    
    if official_match:
        ml_data = predict_multiplier(official_match.district, float(official_match.rate_sqm), official_match.effective_date)
        return {
            "location": f"{official_match.locality}, {official_match.district}",
            "district": official_match.district,
            "estimated_rate_sqm": int(official_match.rate_sqm),
            "growth_potential": "High (Verified)",
            "risk_factors": "Official government rate. No heuristic estimation risk.",
            "smart_insight": f"This is an EXACT official circle rate for {official_match.property_type} property in {official_match.tehsil} tehsil, effective since {official_match.effective_date.strftime('%Y-%m-%d')}.",
            "source": "Official IGRS Data Pipeline",
            "effective_date": official_match.effective_date.isoformat(),
            "predicted_multiplier": ml_data["predicted_multiplier"],
            "ml_confidence": ml_data["confidence"]
        }
    
    # 1. Check Database Cache First (Heuristic Fallback)
    cached_entry = db.query(CachedRate).filter(CachedRate.location_query == query_lower).first()
    
    if cached_entry:
        # Check if data is fresher than 30 days
        age_in_days = (datetime.datetime.utcnow() - cached_entry.updated_at).days
        if age_in_days < 30:
            dist = query.split(",")[-1].strip() if "," in query else query
            ml_data = predict_multiplier(dist, float(cached_entry.estimated_rate_sqm), cached_entry.updated_at)
            return {
                "location": query.title(),
                "district": dist,
                "estimated_rate_sqm": cached_entry.estimated_rate_sqm,
                "growth_potential": cached_entry.growth_potential,
                "risk_factors": cached_entry.risk_factors,
                "smart_insight": cached_entry.smart_insight,
                "source": "Database Cache (0 latency)",
                "effective_date": cached_entry.updated_at.isoformat(),
                "predicted_multiplier": ml_data["predicted_multiplier"],
                "ml_confidence": ml_data["confidence"]
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
    
    dist = query.split(",")[-1].strip() if "," in query else query
    ml_data = predict_multiplier(dist, float(scraped_data["estimated_rate_sqm"]), datetime.datetime.utcnow())
    return {
        "location": query.title(),
        "district": dist,
        "estimated_rate_sqm": scraped_data["estimated_rate_sqm"],
        "growth_potential": scraped_data["growth_potential"],
        "risk_factors": scraped_data["risk_factors"],
        "smart_insight": scraped_data["smart_insight"],
        "source": scraped_data["source"],
        "effective_date": datetime.datetime.utcnow().isoformat(),
        "predicted_multiplier": ml_data["predicted_multiplier"],
        "ml_confidence": ml_data["confidence"]
    }
