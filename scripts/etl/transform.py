"""
transform.py

HolyWay Data Engineering Pipeline — Step 2: Transform + Validate

Reads the raw Firestore snapshot (raw/firestore/churches.json) and produces
clean, analytics-friendly CSV datasets plus a data-quality report.

Input:
    raw/firestore/churches.json          (never modified)

Output:
    processed/churches.csv               (one row per church)
    processed/services.csv               (one row per service-language)
    processed/data_quality_report.json   (summary quality metrics)

Usage:
    pip install -r requirements.txt
    python scripts/etl/transform.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
RAW_FILE = PROJECT_ROOT / "raw" / "firestore" / "churches.json"
OUTPUT_DIR = PROJECT_ROOT / "processed"
CHURCHES_CSV = OUTPUT_DIR / "churches.csv"
SERVICES_CSV = OUTPUT_DIR / "services.csv"
QUALITY_REPORT = OUTPUT_DIR / "data_quality_report.json"


# ---------------------------------------------------------------------------
# 1. Load raw data
# ---------------------------------------------------------------------------

def load_raw_data() -> list[dict]:
    """Load the raw churches.json. Never modifies the file."""
    if not RAW_FILE.exists():
        print(f"\n❌  Raw data file not found: {RAW_FILE}")
        print("   Run the extraction first:  npm run extract\n")
        sys.exit(1)

    with open(RAW_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📂  Loaded {len(data)} raw document(s) from {RAW_FILE.name}")
    return data


# ---------------------------------------------------------------------------
# 2. Build churches DataFrame
# ---------------------------------------------------------------------------

# Flat fields to include in churches.csv (all genuinely exist in the source)
CHURCH_COLUMNS = [
    "_firestoreId",
    "name",
    "churchType",
    "denomination",
    "archdiocese",
    "city",
    "address",
    "latitude",
    "longitude",
    "status",
    "website",
    "phone",
]


def build_churches_df(raw_data: list[dict]) -> pd.DataFrame:
    """
    Build a flat churches DataFrame — one row per church.

    Only safe, deterministic transformations are applied:
    - Strip leading/trailing whitespace from text fields.
    - Add derived columns: language_count, service_count.
    - No field renaming, no fuzzy matching, no value invention.
    """
    rows = []
    for doc in raw_data:
        row = {}
        for col in CHURCH_COLUMNS:
            row[col] = doc.get(col)
        # languages as a semicolon-joined string (preserves all values)
        langs = doc.get("languages", [])
        row["languages"] = "; ".join(langs) if isinstance(langs, list) else ""
        row["language_count"] = len(langs) if isinstance(langs, list) else 0

        # Count total service entries across all days
        mt = doc.get("massTimings", {})
        service_count = 0
        if isinstance(mt, dict):
            for day_entries in mt.values():
                if isinstance(day_entries, list):
                    service_count += len(day_entries)
        row["service_count"] = service_count

        rows.append(row)

    df = pd.DataFrame(rows)

    # --- Safe text cleanup: strip whitespace from string columns ---
    text_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in text_cols:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    return df


# ---------------------------------------------------------------------------
# 3. Build services DataFrame
# ---------------------------------------------------------------------------

def build_services_df(raw_data: list[dict]) -> pd.DataFrame:
    """
    Flatten the nested massTimings into one row per service-language.

    A service entry with multiple languages is exploded into separate rows,
    each sharing the same church_id, day, and time.

    Fields: church_id, church_name, day, time, language, note
    """
    rows = []
    for doc in raw_data:
        church_id = doc.get("_firestoreId", "")
        church_name = doc.get("name", "")
        if isinstance(church_name, str):
            church_name = church_name.strip()

        mt = doc.get("massTimings", {})
        if not isinstance(mt, dict):
            continue

        for day_key, entries in mt.items():
            if not isinstance(entries, list):
                continue
            # Capitalize day key for readability (sunday → Sunday)
            day_label = day_key.capitalize()

            for entry in entries:
                if not isinstance(entry, dict):
                    continue

                time_val = entry.get("time", "")
                if isinstance(time_val, str):
                    time_val = time_val.strip()

                note_val = entry.get("note", "")
                if isinstance(note_val, str):
                    note_val = note_val.strip()

                languages = entry.get("languages", [])
                if not isinstance(languages, list) or len(languages) == 0:
                    # Still create a row even if no language is listed
                    rows.append({
                        "church_id": church_id,
                        "church_name": church_name,
                        "day": day_label,
                        "time": time_val,
                        "language": "",
                        "note": note_val,
                    })
                else:
                    # One row per language
                    for lang in languages:
                        lang_val = lang.strip() if isinstance(lang, str) else lang
                        rows.append({
                            "church_id": church_id,
                            "church_name": church_name,
                            "day": day_label,
                            "time": time_val,
                            "language": lang_val,
                            "note": note_val,
                        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. Validation
# ---------------------------------------------------------------------------

def validate(
    raw_data: list[dict],
    churches_df: pd.DataFrame,
    services_df: pd.DataFrame,
) -> dict:
    """
    Run validation checks and build a data-quality report.

    Checks:
    1. Every church has a Firestore document ID.
    2. Church names are present where possible.
    3. Latitude is between -90 and 90 (when not null).
    4. Longitude is between -180 and 180 (when not null).
    5. Every service row has a valid church_id.
    6. Service rows have day and time where the source provides them.
    7. No unexpected loss of church records.
    """
    report = {}
    report["transformation_timestamp"] = datetime.now(timezone.utc).isoformat()
    report["raw_document_count"] = len(raw_data)
    report["processed_church_count"] = len(churches_df)
    report["processed_service_count"] = len(services_df)

    # --- Missing values by important field ---
    missing = {}
    for col in ["_firestoreId", "name", "denomination", "city", "churchType",
                 "status", "archdiocese", "latitude", "longitude", "website", "phone"]:
        if col in churches_df.columns:
            null_count = int(churches_df[col].isna().sum())
            empty_count = int((churches_df[col] == "").sum()) if churches_df[col].dtype == "object" else 0
            missing[col] = null_count + empty_count
    report["missing_values_by_field"] = missing

    # --- Coordinate validation ---
    lat = churches_df["latitude"].dropna()
    lon = churches_df["longitude"].dropna()
    invalid_lat = int(((lat < -90) | (lat > 90)).sum())
    invalid_lon = int(((lon < -180) | (lon > 180)).sum())
    report["coordinates"] = {
        "churches_with_coordinates": int(lat.count()),
        "churches_without_coordinates": int(churches_df["latitude"].isna().sum()),
        "invalid_latitude_count": invalid_lat,
        "invalid_longitude_count": invalid_lon,
    }

    # --- Duplicate Firestore IDs ---
    id_dupes = churches_df["_firestoreId"].duplicated(keep=False)
    report["duplicate_firestore_id_count"] = int(id_dupes.sum())

    # --- massTimings coverage ---
    has_services = int((churches_df["service_count"] > 0).sum())
    report["churches_with_mass_timings"] = has_services
    report["churches_without_mass_timings"] = len(churches_df) - has_services

    # --- Service-level checks ---
    service_issues = {}
    if len(services_df) > 0:
        service_issues["missing_church_id"] = int((services_df["church_id"] == "").sum())
        service_issues["missing_day"] = int((services_df["day"] == "").sum())
        service_issues["missing_time"] = int((services_df["time"] == "").sum())
        service_issues["missing_language"] = int((services_df["language"] == "").sum())
    report["service_validation"] = service_issues

    # --- Record reconciliation ---
    report["reconciliation"] = {
        "raw_count": len(raw_data),
        "processed_count": len(churches_df),
        "difference": len(raw_data) - len(churches_df),
        "note": (
            "Counts match — no records lost or added."
            if len(raw_data) == len(churches_df)
            else "Counts differ — investigate."
        ),
    }

    return report


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------

def main():
    # Ensure UTF-8 output on Windows
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    start = datetime.now(timezone.utc)

    print("")
    print("═══════════════════════════════════════════════════")
    print("  HolyWay Data Pipeline — Transform + Validate")
    print("═══════════════════════════════════════════════════")
    print("")

    # --- Load ---
    raw_data = load_raw_data()

    # --- Transform ---
    print("\n🔄  Building churches dataset…")
    churches_df = build_churches_df(raw_data)
    print(f"   → {len(churches_df)} church row(s)")

    print("🔄  Building services dataset…")
    services_df = build_services_df(raw_data)
    print(f"   → {len(services_df)} service row(s)")

    # --- Validate ---
    print("\n✅  Running validation checks…")
    report = validate(raw_data, churches_df, services_df)

    # --- Write output ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    churches_df.to_csv(CHURCHES_CSV, index=False, encoding="utf-8")
    print(f"\n💾  Wrote {CHURCHES_CSV}")

    services_df.to_csv(SERVICES_CSV, index=False, encoding="utf-8")
    print(f"💾  Wrote {SERVICES_CSV}")

    with open(QUALITY_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"📋  Wrote {QUALITY_REPORT}")

    # --- Summary ---
    end = datetime.now(timezone.utc)
    print("")
    print("───────────────────────────────────────────────────")
    print(f"  Churches : {len(churches_df)}")
    print(f"  Services : {len(services_df)}")
    print(f"  Duration : {(end - start).total_seconds():.1f}s")
    print("───────────────────────────────────────────────────")

    # Print key quality findings
    coords = report["coordinates"]
    print(f"\n  📍 Coordinates: {coords['churches_with_coordinates']} present, "
          f"{coords['churches_without_coordinates']} missing")
    if coords["invalid_latitude_count"] or coords["invalid_longitude_count"]:
        print(f"  ⚠️  Invalid coords: {coords['invalid_latitude_count']} lat, "
              f"{coords['invalid_longitude_count']} lon")

    recon = report["reconciliation"]
    if recon["difference"] == 0:
        print(f"  ✅ Record reconciliation: {recon['raw_count']} raw → "
              f"{recon['processed_count']} processed (no loss)")
    else:
        print(f"  ⚠️  Record reconciliation: {recon['raw_count']} raw → "
              f"{recon['processed_count']} processed (diff: {recon['difference']})")

    print("")


if __name__ == "__main__":
    main()
