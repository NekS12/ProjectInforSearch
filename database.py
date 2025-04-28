import sqlite3

def init_db():
    conn = sqlite3.connect("searches.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            product_name TEXT,
            price INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_search(query, product_name, price):
    conn = sqlite3.connect("searches.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO searches (query, product_name, price)
        VALUES (?, ?, ?)
    ''', (query, product_name, price))
    conn.commit()
    conn.close()
