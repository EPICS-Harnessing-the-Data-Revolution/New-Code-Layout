"""
custom_graph.py
Safely query Measurements.db and plot one selected variable over time.
Automatically finds Measurements.db at the repository root.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys

# --- CONFIG ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def find_repo_root(start_dir, repo_name="New-Code-Layout"):
    """Go up folders until we find the repo root."""
    current = start_dir
    while True:
        if os.path.basename(current) == repo_name:
            return current
        parent = os.path.dirname(current)
        if parent == current:  # reached root of filesystem
            return None
        current = parent

def find_database(repo_root, db_name="Measurements.db"):
    """Search for Measurements.db in the repo root."""
    db_path = os.path.join(repo_root, db_name)
    if os.path.exists(db_path):
        return db_path
    return None

# --- Locate repository root ---
REPO_ROOT = find_repo_root(SCRIPT_DIR)
if not REPO_ROOT:
    print("ERROR: Could not determine repository root.")
    sys.exit(1)

DB_PATH = find_database(REPO_ROOT)
if not DB_PATH:
    print(f"ERROR: Could not find Measurements.db at repo root: {REPO_ROOT}")
    sys.exit(1)

print(f"\nFound database at: {DB_PATH}")

# -----------------------
# Helper functions
# -----------------------

def list_tables(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [r[0] for r in cur.fetchall()]

def list_columns(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    return [r[1] for r in cur.fetchall()]

def detect_time_format(df):
    if df.empty:
        return "string"
    first_val = df['datetime'].iloc[0]
    try:
        int(first_val)
        return 'epoch'
    except (ValueError, TypeError):
        return 'string'

def query_data(conn, table, start_epoch, end_epoch):
    df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 1;", conn)
    fmt = detect_time_format(df)

    if fmt == 'epoch':
        query = f"SELECT * FROM {table} WHERE datetime BETWEEN ? AND ?"
        df = pd.read_sql_query(query, conn, params=(start_epoch, end_epoch))
        df['datetime'] = pd.to_datetime(df['datetime'], unit='s', errors='coerce')
    else:
        start_dt = datetime.fromtimestamp(start_epoch).strftime("%Y-%m-%d %H:%M:%S")
        end_dt = datetime.fromtimestamp(end_epoch).strftime("%Y-%m-%d %H:%M:%S")
        query = f"SELECT * FROM {table} WHERE datetime BETWEEN ? AND ?"
        df = pd.read_sql_query(query, conn, params=(start_dt, end_dt))
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

    return df

# -----------------------
# Main logic
# -----------------------

def main():
    conn = sqlite3.connect(DB_PATH)

    # List tables
    tables = list_tables(conn)
    if not tables:
        print("\nERROR: No tables found in this database!")
        conn.close()
        sys.exit(1)

    print("\nAvailable tables (locations):")
    for i, t in enumerate(tables, 1):
        print(f"{i}. {t}")

    # Choose table
    table_choice = int(input("\nSelect a table by number: ")) - 1
    table = tables[table_choice]

    # Choose column
    columns = list_columns(conn, table)
    print("\nAvailable columns:")
    for i, c in enumerate(columns, 1):
        print(f"{i}. {c}")
    col_choice = int(input("Select a column to plot by number: ")) - 1
    column = columns[col_choice]

    # Date range
    start_input = input("\nEnter start date (YYYY-MM-DD or epoch): ")
    end_input = input("Enter end date (YYYY-MM-DD or epoch): ")

    try:
        start_epoch = int(start_input)
    except ValueError:
        start_epoch = int(datetime.strptime(start_input, "%Y-%m-%d").timestamp())

    try:
        end_epoch = int(end_input)
    except ValueError:
        end_epoch = int(datetime.strptime(end_input, "%Y-%m-%d").timestamp())

    # Query & plot
    df = query_data(conn, table, start_epoch, end_epoch)
    conn.close()

    if column not in df.columns:
        print(f"\nError: Column '{column}' not found in table '{table}'")
        return

    if df.empty:
        print(f"\nNo data found for {table} between the specified dates.")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(df['datetime'], df[column], marker='o', linestyle='-', markersize=3)
    plt.title(f"{column} over time ({table})")
    plt.xlabel("Datetime")
    plt.ylabel(column)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
