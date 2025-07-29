from flask import Flask, render_template, request, redirect, url_for, jsonify, render_template, g
import pulp
import requests
import random
import os
import json
from geopy.distance import geodesic
from flask_cors import CORS
import sqlite3

from app.calculator.optimizer import solve_shopping_ip, ALL_ITEMS
from app.db.query import get_all_products, get_product_prices, get_stores_nearby, get_products_grouped_by_category

app = Flask(__name__)
CORS(app)

DATABASE = 'db/basketroute.db'
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
    db_path = os.path.join(os.path.dirname(__file__), 'db', 'basketroute.db')
    conn = sqlite3.connect(db_path)
    return conn

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

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