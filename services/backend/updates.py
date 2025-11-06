"""
updates.py
Pulls all new data via DataSourceManager and generates tables for each dataset/location.
"""
from services.backend.datasources.manager import DataSourceManager
from services.backend.sqlclasses import _get_db_connection as get_connection
import os
import re
import sqlite3

# optional graph/table helper
try:
    from services.backend.graphgeneration.createCustom import makeTable
except Exception:
    makeTable = None


def normalize_field(name: str) -> str:
    field = name.lower()
    field = re.sub(r"[\/\-\s]+", "_", field)
    field = re.sub(r"[^0-9a-z_]", "", field)
    if re.match(r"^\d", field):
        field = "_" + field
    return field


def ensure_table_and_column(curr: sqlite3.Cursor, table: str, column: str):
    # ensure table exists
    curr.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table} (
            datetime TEXT NOT NULL,
            location TEXT NOT NULL,
            PRIMARY KEY(datetime, location)
        )
        """
    )
    # ensure column exists
    curr.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in curr.fetchall()]
    if column not in cols:
        curr.execute(f'ALTER TABLE {table} ADD COLUMN "{column}" REAL')


def sql_store(conn: sqlite3.Connection, curr: sqlite3.Cursor, location: str, dataset: str, times, values, table="measurements"):
    """
    Store times/values into measurements table under normalized column for dataset.
    """
    if not times or not values:
        return
    field = normalize_field(dataset)
    ensure_table_and_column(curr, table, field)

    for t, v in zip(times, values):
        # insert row if missing
        curr.execute(
            f"INSERT OR IGNORE INTO {table} (datetime, location) VALUES (?, ?)",
            (t, location),
        )
        # update value
        curr.execute(
            f'UPDATE {table} SET "{field}" = ? WHERE datetime = ? AND location = ?',
            (None if v is None else v, t, location),
        )
    conn.commit()


def dictpull(conn: sqlite3.Connection, curr: sqlite3.Cursor, dataset: str, location: str, table="measurements"):
    """
    Return (times, values) for a dataset/location from measurements table.
    """
    field = normalize_field(dataset)
    try:
        curr.execute(
            f'SELECT datetime, "{field}" FROM {table} WHERE location=? ORDER BY datetime ASC',
            (location,),
        )
    except sqlite3.Error:
        return [], []
    rows = curr.fetchall()
    times = [r[0] for r in rows]
    values = [r[1] for r in rows]
    return times, values


def main(num_days: int = 30):
    manager = DataSourceManager()

    # establish DB connection from project's sqlclasses
    conn, curr = get_connection()

    # Pull everything once via manager (manager should call each source.store internally)
    print(f"Pulling last {num_days} days from all sources...")
    try:
        manager.pull_all_data(num_days=num_days)
    except Exception as e:
        print(f"Error during manager.pull_all_data: {e}")

    # After pulling/storing, iterate sources/locations and generate tables per dataset
    locations_map = manager.location_sets
    sources = list(manager.sources.keys())

    for source in sources:
        data_source = manager.get_source(source)
        locs = locations_map.get(source, [])
        if not locs:
            continue

        # determine display dataset names (what is stored as columns)
        if hasattr(data_source, "datasets") and isinstance(data_source.datasets, dict):
            # mapping like {code: display_name} -> use display_name for DB column
            dataset_display = list(data_source.datasets.values())
        elif hasattr(data_source, "dataset_map") and isinstance(data_source.dataset_map, dict):
            dataset_display = list(data_source.dataset_map.keys())
        else:
            dataset_display = []

        for location in locs:
            print(f"Generating tables for {location} from source {source}...")
            for dataset in dataset_display:
                times, values = dictpull(conn, curr, dataset, location)
                if times and values:
                    # write table using helper if available, otherwise print a small summary
                    title = f"{location} {dataset} Table"
                    if makeTable:
                        try:
                            makeTable([values], title)
                        except Exception as e:
                            print(f"makeTable error for {title}: {e}")
                    else:
                        print(f"[TABLE] {title}  rows={len(times)}  sample_times={times[:3]} sample_values={values[:3]}")

    conn.close()
    print("All updates and table generation complete.")

def get_last_date(conn, table: str, location: str, column: str):
    """
    Return the most recent datetime for a given (table, location, column) as a datetime.datetime,
    or None if no value exists. Handles several common timestamp string formats safely.
    """
    curr = conn.cursor()
    try:
        curr.execute(
            f"SELECT MAX(datetime) FROM {table} WHERE location=? AND {column} IS NOT NULL",
            (location,),
        )
        row = curr.fetchone()
        if not row or not row[0]:
            return None

        ts = row[0]
        # parse timestamp robustly
        from datetime import datetime

        # Try ISO first (handles 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS' and trailing Z)
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            pass

        # Try common formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(ts, fmt)
            except Exception:
                continue

        # If parsing fails, return None (caller should handle)
        return None

    except Exception as e:
        # Keep this simple and visible in logs/output
        print(f"get_last_date error querying {table}.{column} for {location}: {e}")
        return None

if __name__ == "__main__":
    main(num_days=100)