# In database.py
import sqlite3
def initialize_database():
    conn = sqlite3.connect('leads.db')  
    cursor = conn.cursor()
    
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_scraped_time TEXT,
            scraped_count INTEGER,
            error_count INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()


initialize_database()