import sqlite3

def create_stores_table(conn):
    c = conn.cursor()
    c.execute('''
    CREATE TABLE Stores (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        address TEXT,
        phone TEXT,
        website TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

def create_products_table(conn):
    c = conn.cursor()
    c.execute('''
    CREATE TABLE Products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        unit TEXT
    )
    ''')

def create_store_products_table(conn):
    c = conn.cursor()
    c.execute('''
    CREATE TABLE StoreProducts (
        store_id INTEGER,
        product_id INTEGER,
        price REAL NOT NULL,
        inventory INTEGER,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (store_id, product_id),
        FOREIGN KEY (store_id) REFERENCES Stores(id),
        FOREIGN KEY (product_id) REFERENCES Products(id)
    )
    ''')

from faker import Faker
import random
import os

def create_fake_data():
    faker = Faker()
    random.seed(42)

    # Paths
    DB_PATH = 'db/basketroute.db'
    os.makedirs('db', exist_ok=True)

    # Database connection
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    NUM_STORES = 20
    NUM_PRODUCTS = 50
    NUM_STORE_PRODUCTS = 300
    categories = ["Dairy", "Produce", "Bakery", "Snacks", "Pantry", "Meat", "Frozen"]
    units = ["L", "kg", "unit", "pack"]

    # Insert Stores
    stores = []
    for _ in range(NUM_STORES):
        name = faker.company()
        lat = round(random.uniform(40.6, 40.7), 6)
        lon = round(random.uniform(-74.0, -73.9), 6)
        address = faker.address().replace("\n", ", ")
        phone = faker.phone_number()
        website = faker.url()
        stores.append((name, lat, lon, address, phone, website))

    cur.executemany('''
    INSERT INTO Stores (name, lat, lon, address, phone, website)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', stores)

    # Insert Products
    products = []
    for _ in range(NUM_PRODUCTS):
        name = faker.word().capitalize() + " " + random.choice(["Milk", "Bread", "Apples", "Rice", "Chicken", "Cheese", "Chips"])
        category = random.choice(categories)
        unit = random.choice(units)
        products.append((name, category, unit))

    cur.executemany('''
    INSERT INTO Products (name, category, unit)
    VALUES (?, ?, ?)
    ''', products)

    # Fetch store and product IDs
    cur.execute("SELECT id FROM Stores")
    store_ids = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT id FROM Products")
    product_ids = [row[0] for row in cur.fetchall()]

    # Insert StoreProducts
    store_products = set()
    entries = []

    while len(entries) < NUM_STORE_PRODUCTS:
        store_id = random.choice(store_ids)
        product_id = random.choice(product_ids)
        if (store_id, product_id) in store_products:
            continue
        store_products.add((store_id, product_id))
        price = round(random.uniform(0.99, 19.99), 2)
        inventory = random.randint(0, 100)
        entries.append((store_id, product_id, price, inventory))

    cur.executemany('''
    INSERT INTO StoreProducts (store_id, product_id, price, inventory)
    VALUES (?, ?, ?, ?)
    ''', entries)

    conn.commit()
    conn.close()


def create_indices(conn):
    c = conn.cursor()

def init_db():
    conn = sqlite3.connect('db/basketroute.db')
    
    create_stores_table(conn)
    create_products_table(conn)
    create_store_products_table(conn)
    create_indices(conn)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # init_db()
    # print("Database initialized successfully.")
    # print("Tables created: Stores, Products, StoreProducts.")
    create_fake_data()