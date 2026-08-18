"""
load_sqlite.py

HolyWay Data Engineering Pipeline - Step 3: Load to SQLite

Reads processed CSV datasets and loads them into a local SQLite database.
Recreates the database and tables on each run to ensure reproducibility.
"""

import sqlite3
import pandas as pd
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
DB_DIR = PROJECT_ROOT / "database"
DB_PATH = DB_DIR / "holyway.db"

CHURCHES_CSV = PROCESSED_DIR / "churches.csv"
SERVICES_CSV = PROCESSED_DIR / "services.csv"

def load_data():
    # Ensure database directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # Connect to SQLite (this creates the file if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    
    cursor = conn.cursor()
    
    # Drop existing tables to ensure reproducibility
    cursor.execute("DROP TABLE IF EXISTS services")
    cursor.execute("DROP TABLE IF EXISTS churches")
    
    # Create churches table
    cursor.execute("""
    CREATE TABLE churches (
        church_id TEXT PRIMARY KEY,
        name TEXT,
        churchType TEXT,
        denomination TEXT,
        archdiocese TEXT,
        city TEXT,
        address TEXT,
        latitude REAL,
        longitude REAL,
        status TEXT,
        website TEXT,
        phone TEXT,
        languages TEXT,
        language_count INTEGER,
        service_count INTEGER
    )
    """)
    
    # Create services table
    cursor.execute("""
    CREATE TABLE services (
        service_id INTEGER PRIMARY KEY AUTOINCREMENT,
        church_id TEXT,
        church_name TEXT,
        day TEXT,
        time TEXT,
        language TEXT,
        note TEXT,
        FOREIGN KEY (church_id) REFERENCES churches(church_id)
    )
    """)
    
    conn.commit()
    
    # Load churches CSV
    if CHURCHES_CSV.exists():
        churches_df = pd.read_csv(CHURCHES_CSV)
        # Rename _firestoreId to church_id to match the database schema
        churches_df.rename(columns={'_firestoreId': 'church_id'}, inplace=True)
        # Load into SQLite
        churches_df.to_sql('churches', conn, if_exists='append', index=False)
        churches_count = len(churches_df)
    else:
        print(f"Warning: {CHURCHES_CSV} not found.")
        churches_count = 0
        
    # Load services CSV
    if SERVICES_CSV.exists():
        services_df = pd.read_csv(SERVICES_CSV)
        # Load into SQLite
        services_df.to_sql('services', conn, if_exists='append', index=False)
        services_count = len(services_df)
    else:
        print(f"Warning: {SERVICES_CSV} not found.")
        services_count = 0
        
    # Validation Queries
    cursor.execute("SELECT COUNT(*) FROM churches")
    db_churches_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM services")
    db_services_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT church_id) FROM churches")
    db_distinct_churches = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM services WHERE church_id NOT IN (SELECT church_id FROM churches)")
    orphan_services_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM churches WHERE latitude IS NULL")
    null_latitude_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM churches WHERE longitude IS NULL")
    null_longitude_count = cursor.fetchone()[0]

    conn.close()

    print("\nSQLite database created successfully.")
    print(f"Database path: {DB_PATH}\n")
    print(f"Church records loaded: {churches_count}")
    print(f"Service records loaded: {services_count}\n")
    
    print("--- Validation Results ---")
    print(f"Rows in churches table: {db_churches_count}")
    print(f"Rows in services table: {db_services_count}")
    print(f"Distinct church IDs in churches table: {db_distinct_churches}")
    print(f"Services with missing/invalid church_id: {orphan_services_count}")
    print(f"Churches with NULL latitude: {null_latitude_count}")
    print(f"Churches with NULL longitude: {null_longitude_count}\n")
    
if __name__ == "__main__":
    load_data()
