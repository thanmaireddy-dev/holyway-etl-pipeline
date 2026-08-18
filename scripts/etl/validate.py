"""
validate.py

HolyWay Data Engineering Pipeline - Data Quality Gate
Validates raw, processed, and SQLite data.
Reports findings and updates processed/data_quality_report.json.
Fails the pipeline ONLY on structural data integrity issues.
"""

import json
import sqlite3
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows cp1252 encoding issue
sys.stdout.reconfigure(encoding="utf-8")

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
RAW_JSON = PROJECT_ROOT / "raw" / "firestore" / "churches.json"
CHURCHES_CSV = PROJECT_ROOT / "processed" / "churches.csv"
SERVICES_CSV = PROJECT_ROOT / "processed" / "services.csv"
DB_PATH = PROJECT_ROOT / "database" / "holyway.db"
REPORT_PATH = PROJECT_ROOT / "processed" / "data_quality_report.json"

def validate_pipeline():
    print("Running Data Quality Validation...\n")
    
    # 1. Load Data
    try:
        with open(RAW_JSON, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        raw_count = len(raw_data)
    except FileNotFoundError:
        print("FAIL: Raw JSON not found.")
        return False
        
    try:
        churches_df = pd.read_csv(CHURCHES_CSV)
        services_df = pd.read_csv(SERVICES_CSV)
    except FileNotFoundError:
        print("FAIL: Processed CSVs not found.")
        return False
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    except Exception as e:
        print(f"FAIL: Database connection failed. {e}")
        return False

    processed_church_count = len(churches_df)
    processed_service_count = len(services_df)
    
    # 2. Structural Integrity Checks (Fail Pipeline if these fail)
    is_valid = True
    
    # Check 1: Record reconciliation
    if raw_count != processed_church_count:
        print(f"Church record reconciliation       FAIL: Raw ({raw_count}) != Processed ({processed_church_count})")
        is_valid = False
    else:
        print("Church record reconciliation       PASS")
        
    # Check 2: Duplicate IDs
    duplicate_ids = churches_df['_firestoreId'].duplicated().sum()
    if duplicate_ids > 0:
        print(f"Duplicate IDs                      FAIL: {duplicate_ids} duplicates found")
        is_valid = False
    else:
        print("Duplicate IDs                      PASS")
        
    # Check 3: Orphan Services
    cursor.execute("SELECT COUNT(*) FROM services WHERE church_id NOT IN (SELECT church_id FROM churches)")
    orphan_count = cursor.fetchone()[0]
    if orphan_count > 0:
        print(f"Orphan services                    FAIL: {orphan_count} orphan services found")
        is_valid = False
    else:
        print("Orphan services                    PASS")

    # Check 4: Invalid Coordinate Ranges
    invalid_lat = len(churches_df[(churches_df['latitude'] < -90) | (churches_df['latitude'] > 90)])
    invalid_lon = len(churches_df[(churches_df['longitude'] < -180) | (churches_df['longitude'] > 180)])
    if invalid_lat > 0 or invalid_lon > 0:
        print(f"Coordinate range validation        FAIL: {invalid_lat} invalid lat, {invalid_lon} invalid lon")
        is_valid = False
    else:
        print("Coordinate range validation        PASS")

    # 3. Data Quality Findings (INFO / WARNING)
    missing_lat = churches_df['latitude'].isna().sum()
    missing_lon = churches_df['longitude'].isna().sum()
    missing_coords = max(missing_lat, missing_lon)
    print(f"Missing coordinates                INFO: {missing_coords}")
    
    # Empty phone string handling
    churches_df['phone_clean'] = churches_df['phone'].replace(['', 'To be updated'], pd.NA)
    missing_phone = churches_df['phone_clean'].isna().sum()
    print(f"Missing phone numbers              INFO: {missing_phone}")

    # Churches without services
    cursor.execute("SELECT COUNT(*) FROM churches WHERE service_count = 0")
    churches_no_services = cursor.fetchone()[0]
    print(f"Churches without services          INFO: {churches_no_services}")

    # Missing service times and languages
    cursor.execute("SELECT COUNT(*) FROM services WHERE time IS NULL OR time = ''")
    missing_service_time = cursor.fetchone()[0]
    print(f"Missing service time               WARNING: {missing_service_time}")

    cursor.execute("SELECT COUNT(*) FROM services WHERE language IS NULL OR language = ''")
    missing_service_lang = cursor.fetchone()[0]
    print(f"Missing service language           WARNING: {missing_service_lang}")

    conn.close()

    # 4. Generate Central Report
    report = {
        "pipeline_timestamp": datetime.now(timezone.utc).isoformat(),
        "extraction_count": raw_count,
        "processed_church_count": processed_church_count,
        "service_count": processed_service_count,
        "duplicate_count": int(duplicate_ids),
        "invalid_coordinate_count": int(invalid_lat + invalid_lon),
        "missing_coordinate_count": int(missing_coords),
        "missing_phone_count": int(missing_phone),
        "churches_without_services_count": int(churches_no_services),
        "missing_service_time_count": int(missing_service_time),
        "missing_service_language_count": int(missing_service_lang),
        "orphan_service_count": int(orphan_count),
        "pipeline_status": "SUCCESS" if is_valid else "FAILED"
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    print(f"\nData Quality Report written to: {REPORT_PATH}")

    if not is_valid:
        print("\nERROR: Structural data integrity checks failed.")
        return False
        
    return True

if __name__ == "__main__":
    import sys
    success = validate_pipeline()
    if not success:
        sys.exit(1)
