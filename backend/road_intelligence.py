import httpx
import math
from typing import List, Dict, Any, Tuple

# Road Classification Mapping & Base Premium Weights
ROAD_CLASSES = {
    "motorway": ("highway", 0.25),
    "trunk": ("highway", 0.25),
    "primary": ("arterial", 0.18),
    "secondary": ("collector", 0.10),
    "tertiary": ("local", 0.03),
    "residential": ("local", 0.03),
    "unclassified": ("local", 0.02),
    "service": ("alley", -0.05),
    "track": ("alley", -0.05),
    "path": ("alley", -0.08)
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def point_to_segment_distance(px, py, x1, y1, x2, y2):
    """
    Calculates the shortest distance from a point to a line segment.
    Uses simple equirectangular approximation for speed over short distances.
    """
    # Convert to approximate flat meters (valid for short distances < 1km)
    dx = (x2 - x1) * 111320 * math.cos(math.radians((y1 + y2) / 2))
    dy = (y2 - y1) * 110574
    
    pdx = (px - x1) * 111320 * math.cos(math.radians((y1 + y2) / 2))
    pdy = (py - y1) * 110574
    
    line_len_sq = dx*dx + dy*dy
    if line_len_sq == 0:
        return math.sqrt(pdx*pdx + pdy*pdy)
        
    # Project point onto line, clamped to [0, 1] segment
    t = max(0, min(1, (pdx * dx + pdy * dy) / line_len_sq))
    
    closest_x = x1 + t * (x2 - x1)
    closest_y = y1 + t * (y2 - y1)
    
    return haversine(py, px, closest_y, closest_x)

async def fetch_road_network(lat: float, lon: float, radius: int = 400) -> List[Dict]:
    """Fetches road geometry within a small radius using Overpass API."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    # 'out geom' returns exact coordinate paths for the roads
    query = f"""
    [out:json];
    way["highway"](around:{radius},{lat},{lon});
    out geom;
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(overpass_url, params={"data": query}, timeout=10.0)
            if response.status_code == 200:
                return response.json().get("elements", [])
    except Exception as e:
        print(f"Road Engine Fetch Error: {e}")
    return []

def analyze_road_intelligence(lat: float, lon: float, roads: List[Dict]) -> Dict[str, Any]:
    """
    Processes raw OSM ways into a Road Intelligence Score.
    """
    if not roads:
        return {
            "road_score": 0.0,
            "road_premium_percent": 0.0,
            "nearest_road_type": "unknown",
            "intersection_bonus": 0.0,
            "dead_end_penalty": 0.0,
            "connectivity_score": 0.0
        }

    min_dist = float('inf')
    nearest_road = None
    total_road_length = 0
    node_usage = {}
    
    # 1. Nearest Road & Geometry Processing
    for road in roads:
        highway_tag = road.get("tags", {}).get("highway", "unclassified")
        geom = road.get("geometry", [])
        if not geom: continue
        
        # Track node intersections
        for node in road.get("nodes", []):
            node_usage[node] = node_usage.get(node, 0) + 1
            
        # Calc length and find nearest segment
        road_len = 0
        for i in range(len(geom) - 1):
            p1 = geom[i]
            p2 = geom[i+1]
            segment_len = haversine(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
            road_len += segment_len
            
            # Distance from pin to this segment
            dist = point_to_segment_distance(lon, lat, p1["lon"], p1["lat"], p2["lon"], p2["lat"])
            if dist < min_dist:
                min_dist = dist
                nearest_road = highway_tag
                
        total_road_length += road_len

    # 2. Road Classification & Base Score
    nearest_road_class, base_score = ROAD_CLASSES.get(nearest_road, ("local", 0.02))
    
    # Distance Penalty: If nearest road is > 100m away, drastically reduce its impact
    distance_decay = max(0, 1 - (min_dist / 150.0))
    road_score = base_score * distance_decay
    
    # 3. Intersection / Corner Detection
    # If any node is used by >=2 roads, it's an intersection.
    intersections = sum(1 for count in node_usage.values() if count > 1)
    intersection_bonus = 0.0
    if intersections > 5:
        intersection_bonus = 0.08  # High connectivity hub
    elif intersections >= 2:
        intersection_bonus = 0.04  # Corner plot potential
        
    # 4. Dead-End Penalty
    dead_end_penalty = 0.0
    if nearest_road_class == "alley" and intersections == 0:
        dead_end_penalty = -0.05
    if min_dist > 80: # Poor access
        dead_end_penalty -= 0.05

    # 5. Connectivity Score
    # 3000 meters of road in a 400m radius is decent urban density
    connectivity_score = min(1.0, total_road_length / 3000.0)
    
    # Compile Final Adjusted Premium
    total_premium = road_score + intersection_bonus + dead_end_penalty
    
    # Cap between -12% and +25%
    total_premium = max(-0.12, min(0.25, total_premium))
    
    return {
        "road_score": round(road_score, 3),
        "road_premium_percent": round(total_premium * 100, 1),
        "nearest_road_type": nearest_road_class,
        "nearest_road_dist_m": round(min_dist, 1),
        "intersection_bonus": round(intersection_bonus, 3),
        "dead_end_penalty": round(dead_end_penalty, 3),
        "connectivity_score": round(connectivity_score, 3)
    }

async def get_road_intelligence(lat: float, lon: float) -> Dict[str, Any]:
    """Main wrapper for FastAPI."""
    roads = await fetch_road_network(lat, lon, 400)
    return analyze_road_intelligence(lat, lon, roads)
