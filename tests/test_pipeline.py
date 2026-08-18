"""
test_pipeline.py

Lightweight testing for the HolyWay Data Engineering Pipeline.
Run via: python tests/test_pipeline.py

Distinguishes between:
1. Structural Tests: Must ALWAYS pass regardless of the source dataset.
2. Baseline Assertions: Document the current state of the dataset (101 churches) 
   and should be updated if the underlying source data legitimately changes.
"""

import sqlite3
import pandas as pd
import sys
from pathlib import Path

# Fix Windows cp1252 encoding issue
sys.stdout.reconfigure(encoding="utf-8")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHURCHES_CSV = PROJECT_ROOT / "processed" / "churches.csv"
SERVICES_CSV = PROJECT_ROOT / "processed" / "services.csv"
DB_PATH = PROJECT_ROOT / "database" / "holyway.db"

def test_pipeline_structure():
    print("Running Structural Tests (Must always pass)...")
    
    # 1-3. Files exist
    assert CHURCHES_CSV.exists(), "churches.csv does not exist"
    assert SERVICES_CSV.exists(), "services.csv does not exist"
    assert DB_PATH.exists(), "SQLite database does not exist"
    
    # Connect to DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 4-5. Tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='churches'")
    assert cursor.fetchone() is not None, "churches table missing from SQLite"
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='services'")
    assert cursor.fetchone() is not None, "services table missing from SQLite"
    
    # 8. No orphan foreign keys
    cursor.execute("SELECT COUNT(*) FROM services WHERE church_id NOT IN (SELECT church_id FROM churches)")
    orphan_count = cursor.fetchone()[0]
    assert orphan_count == 0, f"Found {orphan_count} orphan services"
    
    # 9-10. Required PK/FK present (no nulls)
    cursor.execute("SELECT COUNT(*) FROM churches WHERE church_id IS NULL")
    null_church_ids = cursor.fetchone()[0]
    assert null_church_ids == 0, "Found null church_id in churches table"

    cursor.execute("SELECT COUNT(*) FROM services WHERE church_id IS NULL")
    null_fks = cursor.fetchone()[0]
    assert null_fks == 0, "Found null church_id foreign keys in services table"

    conn.close()
    print("✅ All structural tests passed.")

def test_current_baseline():
    print("\nRunning Current Baseline Assertions (Validates today's known dataset)...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 6. Church count is 101
    cursor.execute("SELECT COUNT(*) FROM churches")
    church_count = cursor.fetchone()[0]
    if church_count != 101:
        print(f"⚠️ Baseline warning: Expected 101 churches, found {church_count}. Update test if intentional.")
    else:
        print("✅ Baseline: Church count is 101")
        
    # 7. Service count is 259
    cursor.execute("SELECT COUNT(*) FROM services")
    service_count = cursor.fetchone()[0]
    if service_count != 259:
        print(f"⚠️ Baseline warning: Expected 259 services, found {service_count}. Update test if intentional.")
    else:
        print("✅ Baseline: Service count is 259")

    conn.close()

if __name__ == "__main__":
    test_pipeline_structure()
    test_current_baseline()
