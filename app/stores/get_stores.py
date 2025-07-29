import overpy
import sqlite3
import math

API = overpy.Overpass()

QUERY = """
[out:json][timeout:25];
area["name"="Brooklyn"]["boundary"="administrative"]->.searchArea;
(
  node["shop"="supermarket"](area.searchArea);
  node["shop"="grocery"](area.searchArea);
  node["brand"="Walmart"](area.searchArea);
  node["brand"="Target"](area.searchArea);
);
out body;
"""

def create_db():
    conn = sqlite3.connect("stores.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            name TEXT,
            chain TEXT,
            address TEXT,
            lat REAL,
            lon REAL,
            zip_code TEXT,
            PRIMARY KEY (name, lat, lon, zip_code)
        );
    """)
    conn.commit()
    return conn

def parse_address(tags):
    parts = [tags.get(k, "") for k in ["addr:housenumber", "addr:street", "addr:city"]]
    return ", ".join(filter(None, parts))

def load_osm_data():
    result = API.query(QUERY)
    conn = create_db()
    cur = conn.cursor()

    counter = 0

    for node in result.nodes:
        name = node.tags.get("name", "Unknown")
        brand = node.tags.get("brand", "Unknown")
        address = parse_address(node.tags)
        lat, lon = node.lat, node.lon
        zip_code = node.tags.get("addr:postcode", "Unknown")

        name = str(name) if name is not None else ""
        brand = str(brand) if brand is not None else ""
        address = str(address) if address is not None else ""
        lat = float(lat) if lat is not None else 0.0
        lon = float(lon) if lon is not None else 0.0
        zip_code = str(zip_code) if zip_code is not None else ""
        if brand != "Unknown":
            cur.execute("INSERT INTO stores (name, chain, address, lat, lon, zip_code) VALUES (?, ?, ?, ?, ?, ?)",
                        (name, brand, address, lat, lon, zip_code))
            counter += 1
    
    conn.commit()
    conn.close()
    print(f"✅ Stored {counter} store locations.")

def get_stores_in_zip(zip_code):
    conn = create_db()
    cur = conn.cursor()
    # cur.execute("SELECT * FROM stores")
    cur.execute("SELECT * FROM stores WHERE zip_code LIKE ?", (f"%{zip_code}%",))
    return cur.fetchall()

def haversine(lat1, lon1, lat2, lon2):
    R = 3959  # miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

def find_stores_nearby(user_lat, user_lon, radius_miles=3):
    conn = sqlite3.connect("stores.db")
    cur = conn.cursor()
    cur.execute("SELECT name, chain, address, lat, lon FROM stores")
    results = []

    for row in cur.fetchall():
        name, chain, address, lat, lon = row
        distance = haversine(user_lat, user_lon, lat, lon)
        if distance <= radius_miles:
            results.append({
                "name": name,
                "chain": chain,
                "address": address,
                "lat": lat,
                "lon": lon,
                "distance_miles": round(distance, 2)
            })

    conn.close()
    return sorted(results, key=lambda x: x["distance_miles"])

if __name__ == "__main__":
    # load_osm_data()
    for store in get_stores_in_zip(""):
        print(store)


