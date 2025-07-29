from geopy.distance import geodesic
import json

def parse_location(location):
    # If location is in 'lat,lon' format, use directly
    try:
        lat, lon = map(float, location.split(','))
        return lat, lon
    except Exception:
        return None

# Load all stores from local file
def load_all_stores():
    with open('stores_manhattan.json', 'r') as f:
        return json.load(f)

# Filter stores by distance from (lat, lon) within radius_km
def filter_stores_by_distance(stores, lat, lon, radius_km, max_stores):
    filtered = []
    for store in stores:
        dist = geodesic((lat, lon), (store['lat'], store['lon'])).km
        if dist <= radius_km:
            filtered.append(store)
        if len(filtered) >= max_stores:
            break
    return filtered
