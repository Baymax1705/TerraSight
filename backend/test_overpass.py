import requests

overpass_url = "http://overpass-api.de/api/interpreter"
overpass_query = """
[out:json][timeout:25];
(
    node["amenity"="school"](around:2000,26.8467,80.9462);
);
out body;
>;
out skel qt;
"""
headers = {
    'User-Agent': 'GeoIntelUP/1.0 (Contact: yashv@example.com)'
}
try:
    response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(response.text[:500])
except Exception as e:
    print(f"Error: {e}")
