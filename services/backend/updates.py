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


if __name__ == "__main__":
    main(num_days=30)



"""



from services.backend.datasources.manager import DataSourceManager
from services.backend.sqlclasses import _get_db_connection as get_connection
from services.backend.datasources.config import LOCATION_TO_TABLE, TABLE_SCHEMAS
from datetime import datetime, timedelta
import csv
import os

LOG_FILE = "update_audit_log.csv"

def get_last_date(conn, table, location, column):
    curr = conn.cursor()
    curr.execute(f"SELECT MAX(datetime) FROM {table} WHERE location=? AND {column} IS NOT NULL", (location,))
    row = curr.fetchone()
    if row and row[0]:
        return datetime.fromisoformat(row[0])
    return None

def log_update(source, location, dataset, start_date, end_date, record_count):
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["timestamp", "source", "location", "dataset", "start_date", "end_date", "records"])
        writer.writerow([datetime.now().isoformat(), source, location, dataset, start_date.isoformat(), end_date.isoformat(), record_count])

def main():
    manager = DataSourceManager()
    conn, _ = get_connection()
    
    sources = manager.sources.keys()
    locations_map = manager.location_sets
    today = datetime.today()
    
    for source in sources:
        data_source = manager.get_source(source)
        for location in locations_map.get(source, []):
            table = LOCATION_TO_TABLE.get(location)
            if not table:
                continue
            if table not in TABLE_SCHEMAS:
                continue
            
            if hasattr(data_source, "datasets"):
                dataset_names = list(data_source.datasets.values())
            elif hasattr(data_source, "dataset_map"):
                dataset_names = list(data_source.dataset_map.keys())
            else:
                dataset_names = []
            
            for dataset in dataset_names:
                sql_field = data_source.datasets.get(dataset) if hasattr(data_source, "datasets") else dataset
                last_date = get_last_date(conn, table, location, sql_field)
                start_date = last_date + timedelta(days=1) if last_date else today - timedelta(days=30)
                
                start_dict = {"year": start_date.strftime("%Y"), "month": start_date.strftime("%m"), "day": start_date.strftime("%d")}
                end_dict = {"year": today.strftime("%Y"), "month": today.strftime("%m"), "day": today.strftime("%d")}
                
                # Pull data and store in SQL
                times, values = data_source.pull_all(start_dict, end_dict)
                
                # Log the update
                record_count = len(times) if times else 0
                log_update(source, location, dataset, start_date, today, record_count)
    
    conn.close()

if __name__ == "__main__":
    main()

"""
