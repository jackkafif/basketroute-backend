from geopy.distance import geodesic
import json
import sqlite3

def parse_location(location):
    # If location is in 'lat,lon' format, use directly
    try:
        lat, lon = map(float, location.split(','))
        return lat, lon
    except Exception:
        return None
    
def get_products_grouped_by_category(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, category, unit FROM Products')
    products = cursor.fetchall()
    conn.close()
    grouped_products = {}
    for product in products:
        product_id, name, category, unit = product
        if category not in grouped_products:
            grouped_products[category] = []
        grouped_products[category].append({
            'id': product_id,
            'name': name,
            'unit': unit
        })
    return grouped_products
    
def get_all_products(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, category, unit FROM Products')
    products = cursor.fetchall()
    conn.close()
    return [{
        'id': product[0],
        'name': product[1],
        'category': product[2],
        'unit': product[3]
    } for product in products]

def get_product_prices(conn, product_name):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sp.store_id, s.name, sp.price, sp.inventory, sp.last_updated
        FROM StoreProducts sp
        JOIN Stores s ON sp.store_id = s.id
        WHERE sp.product_id = (SELECT id FROM Products WHERE name = ?)
    ''', (product_name,))
    prices = cursor.fetchall()
    conn.close()
    return [{
        'store_id': price[0],
        'store_name': price[1],
        'price': price[2],
        'inventory': price[3],
        'last_updated': price[4]
    } for price in prices]

def get_stores_nearby(location, radius_km=5, max_stores=20):
    lat_lon = parse_location(location)
    if not lat_lon:
        return []
    lat, lon = lat_lon
    conn = sqlite3.connect('db/basketroute.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, lat, lon, address, phone, websit, (
                   6371 * acos(
                cos(radians(?)) * cos(radians(lat)) * cos(radians(lon) - radians(?)) +
                sin(radians(?)) * sin(radians(lat))
            )
        ) AS distance_km
        FROM Stores
        WHERE distance_km <= ?
        ORDER BY distance_km ASC
        LIMIT ?
    ''', (lat, lon, lat, radius_km, max_stores))
    stores = cursor.fetchall()
    conn.close()
    return [{
        'id': store[0],
        'name': store[1],
        'lat': store[2],
        'lon': store[3],
        'address': store[4],
        'phone': store[5],
        'website': store[6],
        'distance_km': store[7]
    } for store in stores]