from flask import Flask, render_template, request, redirect, url_for, jsonify, render_template, g
import pulp
import requests
import random
import os
import json
from geopy.distance import geodesic
from flask_cors import CORS
import sqlite3

from app.calculator.optimizer import solve_shopping_ip, translate_ip_result_to_plan
from app.db.query import (
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
    item_names = data.get('items', [])
    store_names = data.get('stores', [])
    print("Received item names:", item_names)
    print("Received store names:", store_names)
    item_store_matrix = build_item_store_matrix(create_connection(), item_names, store_names)
    print("Item-Store Matrix:", item_store_matrix)
    if not item_store_matrix:
        return jsonify({'error': 'No valid item-store matrix found'}), 400

    if not item_names or not store_names or not item_store_matrix:
        return jsonify({'error': 'Invalid input data'}), 400

    plans, total_cost = solve_shopping_ip(item_names, store_names, item_store_matrix)
    translated = translate_ip_result_to_plan(plans)

    results = {}
    results['Plan'] = translated
    results['Cost'] = total_cost

    print(json.dumps(results))

    return jsonify(results)

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