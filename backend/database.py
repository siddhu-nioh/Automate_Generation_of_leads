

import sqlite3

def init_progress_table():
    """Initialize a table to track scraping progress."""
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS progress
                      (id INTEGER PRIMARY KEY, 
                       last_scraped_time TEXT, 
                       scraped_count INTEGER, 
                       error_count INTEGER)''')
    conn.commit()
    conn.close()

def get_progress_from_db():
    """Fetch the last scraping progress from the database."""
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute("SELECT last_scraped_time, scraped_count, error_count FROM progress ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, 0, 0)

def update_progress(last_scraped_time, scraped_count, error_count):
    """Update the scraping progress in the database."""
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO progress (last_scraped_time, scraped_count, error_count) VALUES (?, ?, ?)", 
                   (last_scraped_time, scraped_count, error_count))
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS leads
                      (id INTEGER PRIMARY KEY, 
                       name TEXT, 
                       link TEXT, 
                       insights TEXT, 
                       email TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    for entry in data:
        cursor.execute("INSERT INTO leads (name, link, insights, email) VALUES (?, ?, ?, ?)",
                       (entry["name"], entry["link"], entry["insights"], entry["email"]))
    conn.commit()
    conn.close()
def get_leads_count():
    """Get the number of leads in the database."""
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0
def fetch_leads():
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads")
    rows = cursor.fetchall()
    conn.close()
    return rows
def is_already_in_db(entry):
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM leads WHERE name = ? OR link = ?", (entry['name'], entry['link']))
    result = cursor.fetchone()
    conn.close()
    return result is not None



def initialize_database():
    conn = sqlite3.connect('database.db')  
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
