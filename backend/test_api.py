import requests
url = 'http://localhost:8000/api/facilities?lat=26.8467&lon=80.9462&radius_m=2000'
try:
    print(requests.get(url).json())
except Exception as e:
    print(e)
