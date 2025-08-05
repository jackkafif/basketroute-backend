from flask import Flask, render_template, request, redirect, url_for, jsonify, render_template, g
import pulp
import requests
import random
import os
import json
from geopy.distance import geodesic
from flask_cors import CORS
import sqlite3

from app.calculator.optimizer import optimize, translate_ip_result_to_plan
from app.calculator.pathOptimize import optimize_path
from app.db.query import (
    get_products_by_names, get_stores_by_names, get_products_by_ids,
    get_all_products, get_product_prices, 
    get_stores_nearby, get_products_grouped_by_category, 
    get_all_stores, get_stores_like, build_item_store_matrix
)

app = Flask(__name__)
CORS(app)

DATABASE = 'db/fake_basketroute.db'
def get_db():
    if not hasattr(g, 'db'):
        g.db = sqlite3.connect(DATABASE)
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def create_connection():
    db_path = os.path.join(os.path.dirname(__file__), DATABASE)
    conn = sqlite3.connect(db_path)
    return conn

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

@app.route('/')
def index():
    conn = create_connection()
    stores = get_all_stores(conn)
    conn = create_connection()
    products = get_all_products(conn)
    conn = create_connection()
    grouped_products = get_products_grouped_by_category(conn)
    return render_template('index.html', stores=stores, products=products, grouped_products=grouped_products)

@app.route('/api/optimize', methods=['POST'])
def optimize_shopping():
    data = request.json
    item_ids_reqs = data.get('items', [])
    items = get_products_by_ids(create_connection(), [item["product_id"] for item in item_ids_reqs])
    item_names = [item['name'] for item in items]
    requirements = [item['quantity'] for item in item_ids_reqs]
    # store_names = data.get('stores', [])
    print("Received item names:", item_names)
    if not item_names:
        return jsonify({'error': 'Item names and store names are required'}), 400
    items = get_products_by_names(create_connection(), item_names)
    stores = get_all_stores(create_connection())
    store_names = [store['name'] for store in stores]
    item_store_matrix = build_item_store_matrix(create_connection(), items, stores)
    print("Item-Store Matrix:", item_store_matrix)
    if not item_store_matrix:
        return jsonify({'error': 'No valid item-store matrix found'}), 400

    if not item_names or not store_names or not item_store_matrix:
        return jsonify({'error': 'Invalid input data'}), 400

    result = optimize(item_store_matrix, requirements)
    if not result:
        return jsonify({'error': 'Optimization failed'}), 500
    translated = translate_ip_result_to_plan(result, items, stores)

    print(json.dumps(translated))
    plan = translated.get('plan', {})
    stores_dict = {store['name']: {"lat" : store['lat'], "lon" : store['lon']} for store in stores}
    store_list = [{'name': store, 'lat': stores_dict[store]['lat'], 'lon': stores_dict[store]['lon']} for store in plan.keys()]
    for store in store_list:
        for s in stores:
            if s['name'] == store['name']:
                store['lat'] = s['lat']
                store['lon'] = s['lon']
                break
    optimized_stores = optimize_path(store_list, starting_point=(40.7128, -74.0060))  # Example starting point (New York City)
    if optimized_stores["status"] != "Optimal":
        return jsonify({'error': 'Path optimization failed'}), 500
    optimized_plan = optimized_stores['ordered_stores']
    distance = optimized_stores['total_distance_meters']
    print("Optimized path:", [s['name'] for s in optimized_plan])
    print("plan :", plan)
    translated['plan'] = [
        {'store': store['name'], 'items': plan[store['name']]} for store in optimized_plan
    ]
    translated['cost'] = result['total_cost']
    translated['distance'] = distance
    print("Translated plan:", translated)

    return jsonify(translated)

@app.route('/api/all_stores')
def all_stores():
    conn = create_connection()
    stores = get_all_stores(conn)
    return jsonify(stores)

@app.route('/api/store_inventories')
def store_inventories():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.name, p.name, sp.price, sp.inventory
        FROM StoreProducts sp
        JOIN Stores s ON sp.store_id = s.id
        JOIN Products p ON sp.product_id = p.id
    ''')
    rows = cursor.fetchall()
    conn.close()

    inventories = {}
    for store_name, product_name, price, inventory in rows:
        if store_name not in inventories:
            inventories[store_name] = []
        inventories[store_name].append({
            'product': product_name,
            'price': price,
            'inventory': inventory
        })
    
    return jsonify(inventories)

@app.route('/api/stores_like/<string:name>')
def stores_like(name):
    conn = create_connection()
    stores = get_stores_like(conn, name)
    return jsonify(stores)

@app.route('/api/products')
def get_products():
    conn = create_connection()
    products = get_all_products(conn)
    return jsonify(products)

@app.route('/api/products_by_category')
def get_products_by_category():
    conn = create_connection()
    grouped_products = get_products_grouped_by_category(conn)
    return jsonify(grouped_products)

@app.route('/api/product_prices/<string:product_name>')
def get_product_prices_by_name(product_name):
    conn = create_connection()
    prices = get_product_prices(conn, product_name)
    if prices:
        return jsonify(prices)
    return jsonify({'error': 'Product not found'}), 404

if __name__ == '__main__':
    app.run(debug=True) 