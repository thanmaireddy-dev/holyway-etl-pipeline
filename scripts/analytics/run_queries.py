"""
run_queries.py

HolyWay Data Engineering Pipeline - Step 4: SQL Analytics

Connects to the local SQLite database and runs analytical queries
from sql/analytics.sql to generate insights and identify data quality issues.
"""

import sqlite3
import pandas as pd
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DB_DIR = PROJECT_ROOT / "database"
DB_PATH = DB_DIR / "holyway.db"
SQL_DIR = PROJECT_ROOT / "sql"
ANALYTICS_SQL = SQL_DIR / "analytics.sql"

def run_analytics():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        print("Please run scripts/etl/load_sqlite.py first.")
        return

    if not ANALYTICS_SQL.exists():
        print(f"Error: SQL file not found at {ANALYTICS_SQL}")
        return

    # Read the SQL file
    with open(ANALYTICS_SQL, 'r') as f:
        sql_content = f.read()

    # Split into individual queries (assuming they are separated by double newlines and comments)
    queries = []
    current_query = []
    current_title = ""
    
    for line in sql_content.split('\n'):
        if line.startswith('-- '):
            if current_query:
                queries.append((current_title, '\n'.join(current_query).strip()))
                current_query = []
            current_title = line[3:]
        elif line.strip() != '':
            current_query.append(line)
            
    if current_query:
        queries.append((current_title, '\n'.join(current_query).strip()))

    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*50)
    print("HolyWay Data Pipeline - SQL Analytics Results")
    print("="*50 + "\n")
    
    # Execute and print each query
    for i, (title, query) in enumerate(queries, 1):
        title_str = f"Query {i}: {title}"
        print(title_str)
        print("-" * len(title_str))
        try:
            df = pd.read_sql_query(query, conn)
            if df.empty:
                print("No results found.\n")
            else:
                print(df.to_string(index=False))
                print()
        except Exception as e:
            print(f"Error executing query: {e}\n")

    conn.close()

if __name__ == "__main__":
    run_analytics()
