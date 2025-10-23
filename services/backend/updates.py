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

#Insert data into SQL
def sql_store(conn, location, dataset, times, values, table="cocorahs"):
    conn, cursor = get_connection()
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
def dictpull(conn, curr, dataset, location, table="cocorahs"):
    curr = conn.cursor()
    curr.execute(
        f"SELECT datetime, {dataset} FROM {table} WHERE location=? ORDER BY datetime ASC",
        (location,),
    )
    rows = curr.fetchall()
    return [{"datetime": row[0], "value": row[1]} for row in rows]



def makeTable (sql_data, dataset, location):
    pass

def main():
    manager = DataSourceManager()
    conn, curr = get_connection()
    
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


            sql_data = dictpull(conn, curr, dataset, location)
            if sql_data:
                makeTable(sql_data, dataset, location)
    
    
    conn.close()
    print("All new data stored and tables generated.")

if __name__ == "__main__":
    main()            
