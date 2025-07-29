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
    
def get_all_products():
    conn = sqlite3.connect('db/basketroute.db')
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

def get_product_prices(store_id, product_id):
    conn = sqlite3.connect('db/basketroute.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT price, inventory, last_updated FROM StoreProducts
        WHERE store_id = ? AND product_id = ?
    ''', (store_id, product_id))
    price_info = cursor.fetchone()
    conn.close()
    if price_info:
        return {
            'price': price_info[0],
            'inventory': price_info[1],
            'last_updated': price_info[2]
        }
    return None

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