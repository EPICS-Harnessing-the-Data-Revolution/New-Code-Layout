#Updates SQL table via pulling data from source files & Creates create graphs for Frontend
"""
updates.py 
Pulls all new data, stores in SQL
"""
from services.backend.datasources.manager import DataSourceManager
from services.backend.sqlclasses import _get_db_connection as get_connection
import matplotlib.pyplot as plt
import pandas as pd
import os
import sqlite3

#Insert data into SQL
def sql_store(conn, location, dataset, times, values, table="measurements"):
    curr = conn.cursor()
    for t, v in zip(times, values):
        try:
            curr.execute(
                f"""
                INSERT OR IGNORE INTO {table} (datetime, location, {dataset})
                VALUES (?, ?, ?)
                """,
                (t, location, v),
            )
        except sqlite3.Error as e:
            print(f"Error storing {dataset} for {location} at {t}: {e}")
    conn.commit()

#Pull existing data from SQL
def dictpull(conn, dataset, location, table="measurements"):
    curr = conn.cursor()
    curr.execute(
        f"SELECT datetime, {dataset} FROM {table} WHERE location=? ORDER BY datetime ASC",
        (location,),
    )
    rows = curr.fetchall()
    return [{"datetime": row[0], "value": row[1]} for row in rows]

def main():
    manager = DataSourceManager()
    conn = get_connection()
    
    #pull data
    manager.pull_all_data(num_days=30)
    
    locations_map = manager.location_sets
    sources = manager.sources.keys()
    
    for source in sources:
        for location in locations_map.get(source, []):
            data_source = manager.get_source(source)
            print(f"\nProcessing {location} from {source}...")
            
            #pull data for location (range input)
            data_source.pull_all({'year': '2023', 'month': '01', 'day': '01'},
                                 {'year': '2023', 'month': '12', 'day': '31'})
            
            #Find datasets
            if hasattr(data_source, "datasets"):
                dataset_names = list(data_source.datasets.values())
            elif hasattr(data_source, "dataset_map"):
                dataset_names = list(data_source.dataset_map.keys())
            else:
                dataset_names = []

            for dataset in dataset_names:
                #Fetch time/values for each one
                times = getattr(data_source, f"{dataset}_times", None)
                values = getattr(data_source, f"{dataset}_values", None)
                
                if times is None or values is None:
                    data_attr = getattr(data_source, "data", {})
                    if dataset in data_attr:
                        times = data_attr[dataset].get("times", [])
                        values = data_attr[dataset].get("values", [])
                
                if times and values:
                    sql_store(conn, location, dataset, times, values)

                
            sql_data = dictpull(conn, dataset, location)
            if sql_data:
                makeTable(sql_data, dataset, location)
    
    
    conn.close()
    print("All new data stored and tables generated.")

if __name__ == "__main__":
    main()          




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

