from flask import Flask, render_template, request, redirect, url_for, jsonify, render_template
import pulp
import requests
import random
import os
import json
from geopy.distance import geodesic
from flask_cors import CORS

from calculator.optimizer import solve_shopping_ip, ALL_ITEMS
from db.query import parse_location, load_all_stores, filter_stores_by_distance

app = Flask(__name__)
CORS(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

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

last_result = None

if __name__ == '__main__':
    app.run(debug=True) 