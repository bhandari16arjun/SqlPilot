import os
import urllib.request
import sqlite3

def setup_database():
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "demo.db")

    # Delete the old synthetic database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed old synthetic demo.db")

    print("Downloading the official Chinook SQLite database...")
    # Reliable source for the Chinook SQLite database
    url = "https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
    
    try:
        urllib.request.urlretrieve(url, db_path)
        print(f"Successfully downloaded Chinook database to {db_path}")
        
        # Verify it's a valid SQLite database by checking its tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Verified {len(tables)} tables in the database: {', '.join(tables)}")
        conn.close()
        
    except Exception as e:
        print(f"Failed to download or verify Chinook database: {e}")
        exit(1)

if __name__ == "__main__":
    setup_database()
