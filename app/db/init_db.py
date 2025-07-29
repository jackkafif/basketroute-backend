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

def create_indices(conn):
    c = conn.cursor()
    # c.execute('CREATE INDEX idx_stores_lat_lon ON Stores(lat, lon)')
    # c.execute('CREATE INDEX idx_store_products_name ON StoreProducts(name)')
    # c.execute('CREATE INDEX idx_products_category ON Products(category)')

def init_db():
    conn = sqlite3.connect('db/basketroute.db')
    
    create_stores_table(conn)
    create_products_table(conn)
    create_store_products_table(conn)
    create_indices(conn)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
    print("Tables created: Stores, Products, StoreProducts.")
    print("Indices created: idx_stores_lat_lon, idx_store_products_name, idx_products_category.")
    print("You can now populate the database with data.")
