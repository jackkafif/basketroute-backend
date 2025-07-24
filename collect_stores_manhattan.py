import requests
import os
import time
import json

GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', 'AIzaSyDanP0j-CShf-0mns9rcu5mHe962WDGYDk')

# Manhattan bounding box (approx): southwest and northeast corners
MANHATTAN_SW = (40.700, -74.027)
MANHATTAN_NE = (40.882, -73.906)

# Google Places API: 60 results max per search (20 per page, 3 pages)
SEARCH_RADIUS = 1500  # meters (max for text search is 50,000, but we use grid for coverage)

# Helper to search for grocery stores in a grid over Manhattan
def collect_stores():
    stores = {}
    lats = [round(x, 3) for x in frange(MANHATTAN_SW[0], MANHATTAN_NE[0], 0.01)]
    lons = [round(x, 3) for x in frange(MANHATTAN_SW[1], MANHATTAN_NE[1], 0.01)]
    i = 0
    for lat in lats:
        for lon in lons:
            print(i)
            i += 1
            url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
            params = {
                'location': f'{lat},{lon}',
                'radius': SEARCH_RADIUS,
                'type': 'supermarket',
                'keyword': 'grocery',
                'key': GOOGLE_MAPS_API_KEY
            }
            page_token = None
            for _ in range(3):  # up to 3 pages
                if page_token:
                    params['pagetoken'] = page_token
                    time.sleep(2)  # Google requires a short wait before using next_page_token
                resp = requests.get(url, params=params)
                if resp.status_code != 200:
                    print(f"Error: {resp.status_code} at {lat},{lon}")
                    continue
                data = resp.json()
                for result in data.get('results', []):
                    name = result.get('name', 'Unknown Store')
                    loc = result['geometry']['location']
                    address = result.get('vicinity', '')
                    place_id = result.get('place_id')
                    key = (name, loc['lat'], loc['lng'])
                    if key not in stores:
                        stores[key] = {
                            'name': name,
                            'lat': loc['lat'],
                            'lon': loc['lng'],
                            'address': address,
                            'place_id': place_id
                        }
                page_token = data.get('next_page_token')
                if not page_token:
                    break
            time.sleep(0.2)  # avoid rate limits
    return list(stores.values())

def frange(start, stop, step):
    x = start
    while x <= stop:
        yield x
        x += step

def main():
    stores = collect_stores()
    with open('stores_manhattan.json', 'w') as f:
        json.dump(stores, f, indent=2)
    print(f"Saved {len(stores)} stores to stores_manhattan.json")

if __name__ == '__main__':
    main() 