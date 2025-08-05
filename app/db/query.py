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
    
def get_all_stores(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, lat, lon, address, phone, website FROM Stores')
    stores = cursor.fetchall()
    conn.close()
    return [{
        'id': store[0],
        'name': store[1],
        'lat': store[2],
        'lon': store[3],
        'address': store[4],
        'phone': store[5],
        'website': store[6]
    } for store in stores]

def get_stores_by_names(conn, store_names):
    cursor = conn.cursor()
    placeholders = ', '.join(['?'] * len(store_names))
    cursor.execute(f'SELECT id, name, lat, lon, address, phone, website FROM Stores WHERE name IN ({placeholders})', store_names)
    stores = cursor.fetchall()
    conn.close()
    return [{
        'id': store[0],
        'name': store[1],
        'lat': store[2],
        'lon': store[3],
        'address': store[4],
        'phone': store[5],
        'website': store[6]
    } for store in stores]

def get_stores_like(conn, name):
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, lat, lon, address, phone, website FROM Stores WHERE name LIKE ?', (f'%{name}%',))
    stores = cursor.fetchall()
    conn.close()
    return [{
        'id': store[0],
        'name': store[1],
        'lat': store[2],
        'lon': store[3],
        'address': store[4],
        'phone': store[5],
        'website': store[6]
    } for store in stores]
    
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

def build_item_store_matrix(conn, items, stores):
    """
    Builds a matrix of items and their corresponding stores with prices and inventory.
    Args:
        items (list of dict): List of item details .
        stores (list of dict): List of store details.
    Returns:
        item_store_matrix (list of tuples (store_id, product_id, price, inventory)): List of tuples where each tuple contains
        the store id, product id, price, and inventory.
    """
    cursor = conn.cursor()
    print(items, stores)
    item_names = [item['name'] for item in items]
    store_ids = [store['id'] for store in stores]
    cursor.execute('''
        SELECT sp.store_id, p.id, sp.price, sp.inventory
        FROM StoreProducts sp
        JOIN Products p ON sp.product_id = p.id
        WHERE p.name IN ({})
    '''.format(','.join(['?'] * len(items))), item_names)
    
    rows = cursor.fetchall()

    item_store_matrix = []
    for store_id, product_id, price, inventory in rows:
        if store_id in store_ids:
            item_store_matrix.append((store_id, product_id, price, inventory))

    conn.close()
    return item_store_matrix
    
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

def get_products_by_names(conn, product_names):
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, category, unit FROM Products WHERE name IN ({})'.format(','.join(['?'] * len(product_names))), product_names)
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