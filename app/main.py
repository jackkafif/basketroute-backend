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
from app.db.query import get_all_products, get_product_prices, get_stores_nearby

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

@app.route('/api/products')
def get_products():
    products = get_all_products()
    return jsonify(products)

if __name__ == '__main__':
    app.run(debug=True) 