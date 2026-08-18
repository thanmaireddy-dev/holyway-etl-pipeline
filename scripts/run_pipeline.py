"""
run_pipeline.py

HolyWay Data Engineering Pipeline - Main Orchestrator
Executes the local ETL pipeline end-to-end.
"""

import subprocess
import sys
import json
from pathlib import Path

# Fix Windows cp1252 encoding issue for unicode characters like ✓ and ✗
sys.stdout.reconfigure(encoding="utf-8")

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
REPORT_PATH = PROJECT_ROOT / "processed" / "data_quality_report.json"

def run_stage(stage_num, total_stages, name, command, cwd=None):
    print(f"\n[{stage_num}/{total_stages}] {name}")
    try:
        # Run the command and capture output
        result = subprocess.run(
            command,
            cwd=cwd or PROJECT_ROOT,
            check=True,
            text=True,
            shell=True
        )
        print(f"✓ {name} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {name} failed with exit code {e.returncode}")
        sys.exit(1)

def print_summary():
    print("\n" + "="*50)
    print("PIPELINE SUMMARY")
    print("="*50)
    
    try:
        with open(REPORT_PATH, 'r', encoding='utf-8') as f:
            report = json.load(f)
            
        print(f"Source records:             {report.get('extraction_count', 'N/A')}")
        print(f"Processed churches:         {report.get('processed_church_count', 'N/A')}")
        print(f"Processed services:         {report.get('service_count', 'N/A')}")
        print(f"SQLite churches:            {report.get('processed_church_count', 'N/A')}")
        print(f"SQLite services:            {report.get('service_count', 'N/A')}")
        print(f"Orphan services:            {report.get('orphan_service_count', 'N/A')}")
        print(f"Missing coordinates:        {report.get('missing_coordinate_count', 'N/A')}")
        
        status = report.get('pipeline_status', 'UNKNOWN')
        print(f"\nPipeline status: {status}")
        
    except FileNotFoundError:
        print("\nCould not find data quality report to generate summary.")
        print("Pipeline status: FAILED")

def main():
    print("="*50)
    print("HOLYWAY DATA PIPELINE")
    print("="*50)

    stages = [
        {
            "name": "EXTRACT",
            "command": "npm run extract"
        },
        {
            "name": "TRANSFORM",
            "command": "python scripts/etl/transform.py"
        },
        {
            "name": "LOAD",
            "command": "python scripts/etl/load_sqlite.py"
        },
        {
            "name": "VALIDATE",
            "command": "python scripts/etl/validate.py"
        },
        {
            "name": "ANALYZE",
            "command": "python scripts/analytics/run_queries.py"
        }
    ]

    total_stages = len(stages)
    
    for i, stage in enumerate(stages, 1):
        run_stage(i, total_stages, stage["name"], stage["command"])
        
    print("\n" + "="*50)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("="*50)
    
    print_summary()

if __name__ == "__main__":
    main()
