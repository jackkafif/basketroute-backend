from flask import Flask, render_template, request, redirect, url_for, jsonify, render_template
import pulp
import requests
import random
import os
import json
from geopy.distance import geodesic
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

ITEM_PRICES = {
    'cheese': 5, 'tomato': 2, 'flour': 1, 'yeast': 1, 'olive oil': 4, 'basil': 2, 'pepperoni': 6, 'mushrooms': 3, 'onion': 1, 'bell pepper': 2
}
ALL_ITEMS = list(ITEM_PRICES.keys())

# Geocode address to (lat, lon) using Google Maps
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', 'YOUR_GOOGLE_MAPS_API_KEY_HERE')
def geocode_address(address):
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'address': address, 'key': GOOGLE_MAPS_API_KEY}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    if not data['results']:
        return None
    loc = data['results'][0]['geometry']['location']
    return float(loc['lat']), float(loc['lng'])

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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        shopping_list = request.form.getlist('shopping_list')
        location = request.form.get('location')
        radius = float(request.form.get('radius'))
        max_stores = int(request.form.get('max_stores') or 3)
        max_distance = float(request.form.get('max_distance') or 20)
        max_time = float(request.form.get('max_time') or 120)
        # Handle coordinates or address
        coords = parse_location(location)
        # if not coords:
        #     coords = geocode_address(location)
        if not coords:
            global last_result
            last_result = {'plan': [], 'total_cost': 0, 'status': 'Invalid address'}
            return redirect(url_for('results'))
        lat, lon = coords
        # Load and filter stores
        all_stores = load_all_stores()
        stores = filter_stores_by_distance(all_stores, lat, lon, radius, max_stores)
        # Assign random inventory for demo
        for store in stores:
            store['inventory'] = {item: random.randint(1, 5) for item in random.sample(ALL_ITEMS, k=random.randint(4, 7))}
        last_result = solve_shopping_ip(shopping_list, stores, max_stores, user_latlon=(lat, lon))
        return redirect(url_for('results'))
    return render_template("index.html")

@app.route('/results')
def results():
    global last_result
    return render_template('results.html', result=last_result)

@app.route('/api/solve', methods=['POST'])
def api_solve():
    data = request.json
    shopping_list = data.get('shopping_list', [])
    location = data.get('location')
    radius = float(data.get('radius', 10)) # Default radius
    max_stores = int(data.get('max_stores', 3))
    max_distance = float(data.get('max_distance', 20))
    max_time = float(data.get('max_time', 120))

    coords = parse_location(location)
    if not coords:
        return jsonify({'status': 'error', 'message': 'Invalid location address'}), 400

    lat, lon = coords
    all_stores = load_all_stores()
    stores = filter_stores_by_distance(all_stores, lat, lon, radius, max_stores)
    for store in stores:
        store['inventory'] = {item: random.randint(1, 5) for item in random.sample(ALL_ITEMS, k=random.randint(4, 7))}

    result = solve_shopping_ip(shopping_list, stores, max_stores, user_latlon=(lat, lon))
    return jsonify(result)

@app.route('/api/groceries', methods=['GET'])
def api_groceries():
    with open('groceries.json', 'r') as f:
        groceries = json.load(f)
    return jsonify(groceries)

def solve_shopping_ip(shopping_list, stores, max_stores, user_latlon=None):
    # Option 1: Minimize total cost
    prob_cost = pulp.LpProblem('GroceryShoppingCost', pulp.LpMinimize)
    x = {s['name']: pulp.LpVariable(f"visit_{s['name']}", cat='Binary') for s in stores}
    y = {(s['name'], item): pulp.LpVariable(f"buy_{item}_at_{s['name']}", cat='Binary')
         for s in stores for item in shopping_list}
    prob_cost += pulp.lpSum([ITEM_PRICES[item] * y[(s['name'], item)] for s in stores for item in shopping_list])
    for item in shopping_list:
        prob_cost += pulp.lpSum([y[(s['name'], item)] for s in stores]) >= 1
    for s in stores:
        for item in shopping_list:
            if item not in s['inventory']:
                prob_cost += y[(s['name'], item)] == 0
    for s in stores:
        for item in shopping_list:
            prob_cost += y[(s['name'], item)] <= x[s['name']]
    prob_cost += pulp.lpSum([x[s['name']] for s in stores]) <= max_stores
    prob_cost.solve()
    plan_cost = []
    for s in stores:
        if x[s['name']].varValue > 0.5:
            items_bought = [item for item in shopping_list if y[(s['name'], item)].varValue > 0.5]
            plan_cost.append({'store': s['name'], 'items': items_bought})
    total_cost = sum(ITEM_PRICES[item] for s in plan_cost for item in s['items'])
    num_stores = len(plan_cost)
    total_distance = 0
    if user_latlon:
        for s in plan_cost:
            store = next(st for st in stores if st['name'] == s['store'])
            total_distance += geodesic(user_latlon, (store['lat'], store['lon'])).km
    # Option 2: Minimize number of stores
    prob_stores = pulp.LpProblem('GroceryShoppingStores', pulp.LpMinimize)
    x2 = {s['name']: pulp.LpVariable(f"visit2_{s['name']}", cat='Binary') for s in stores}
    y2 = {(s['name'], item): pulp.LpVariable(f"buy2_{item}_at_{s['name']}", cat='Binary')
         for s in stores for item in shopping_list}
    prob_stores += pulp.lpSum([x2[s['name']] for s in stores])
    for item in shopping_list:
        prob_stores += pulp.lpSum([y2[(s['name'], item)] for s in stores]) >= 1
    for s in stores:
        for item in shopping_list:
            if item not in s['inventory']:
                prob_stores += y2[(s['name'], item)] == 0
    for s in stores:
        for item in shopping_list:
            prob_stores += y2[(s['name'], item)] <= x2[s['name']]
    prob_stores += pulp.lpSum([x2[s['name']] for s in stores]) <= max_stores
    prob_stores.solve()
    plan_stores = []
    for s in stores:
        if x2[s['name']].varValue > 0.5:
            items_bought = [item for item in shopping_list if y2[(s['name'], item)].varValue > 0.5]
            plan_stores.append({'store': s['name'], 'items': items_bought})
    total_cost2 = sum(ITEM_PRICES[item] for s in plan_stores for item in s['items'])
    num_stores2 = len(plan_stores)
    total_distance2 = 0
    if user_latlon:
        for s in plan_stores:
            store = next(st for st in stores if st['name'] == s['store'])
            total_distance2 += geodesic(user_latlon, (store['lat'], store['lon'])).km
    # Option 3: Minimize total distance (if user location is known)
    plan_distance = []
    total_cost3 = None
    num_stores3 = None
    total_distance3 = None
    if user_latlon:
        prob_dist = pulp.LpProblem('GroceryShoppingDistance', pulp.LpMinimize)
        x3 = {s['name']: pulp.LpVariable(f"visit3_{s['name']}", cat='Binary') for s in stores}
        y3 = {(s['name'], item): pulp.LpVariable(f"buy3_{item}_at_{s['name']}", cat='Binary')
             for s in stores for item in shopping_list}
        prob_dist += pulp.lpSum([geodesic(user_latlon, (s['lat'], s['lon'])).km * x3[s['name']] for s in stores])
        for item in shopping_list:
            prob_dist += pulp.lpSum([y3[(s['name'], item)] for s in stores]) >= 1
        for s in stores:
            for item in shopping_list:
                if item not in s['inventory']:
                    prob_dist += y3[(s['name'], item)] == 0
        for s in stores:
            for item in shopping_list:
                prob_dist += y3[(s['name'], item)] <= x3[s['name']]
        prob_dist += pulp.lpSum([x3[s['name']] for s in stores]) <= max_stores
        prob_dist.solve()
        for s in stores:
            if x3[s['name']].varValue > 0.5:
                items_bought = [item for item in shopping_list if y3[(s['name'], item)].varValue > 0.5]
                plan_distance.append({'store': s['name'], 'items': items_bought})
        total_cost3 = sum(ITEM_PRICES[item] for s in plan_distance for item in s['items'])
        num_stores3 = len(plan_distance)
        total_distance3 = 0
        for s in plan_distance:
            store = next(st for st in stores if st['name'] == s['store'])
            total_distance3 += geodesic(user_latlon, (store['lat'], store['lon'])).km
    return {
        'min_cost': {
            'plan': plan_cost,
            'total_cost': total_cost,
            'num_stores': num_stores,
            'total_distance': total_distance,
            'status': pulp.LpStatus[prob_cost.status],
            'label': 'Minimize Cost'
        },
        'min_stores': {
            'plan': plan_stores,
            'total_cost': total_cost2,
            'num_stores': num_stores2,
            'total_distance': total_distance2,
            'status': pulp.LpStatus[prob_stores.status],
            'label': 'Minimize Number of Stores'
        },
        'min_distance': {
            'plan': plan_distance,
            'total_cost': total_cost3,
            'num_stores': num_stores3,
            'total_distance': total_distance3,
            'status': pulp.LpStatus[prob_dist.status] if user_latlon else None,
            'label': 'Minimize Distance'
        } if user_latlon else None
    }

last_result = None

if __name__ == '__main__':
    app.run(debug=True) 