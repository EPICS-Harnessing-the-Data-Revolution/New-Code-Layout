import os
import requests
import json
import sqlite3
import pandas as pd
from abc import ABC, abstractmethod
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Any, Optional, Union
from services.backend.datasources.config import station_ids
from services.backend.sqlclasses import updateDictionary


class DataSource(ABC):
    def __init__(self, name, data_type):
        self.name = name
        self.data_type = data_type
        self.station_ids = station_ids

    @abstractmethod
    def fetch(self, location = None, dataset = None, start_date = None, end_date = None):
        pass

    @abstractmethod
    def process(self, raw_data = None, location = None, dataset = None):
        """
        Process the raw data into a standardized format.
        Must be implemented by derived classes.
        """
        pass

    def store(self, times = None, values= None, location= None, dataset= None):
        """
        Store the processed data in the sql database.
        """
        updateDictionary(times, values, location, dataset, self.data_type)

    def pull(self, location= None, dataset= None, start_date= None, end_date= None):
        """
        Main method to pull and store data from this source.
        """

        raw_data = self.fetch(location, dataset, start_date, end_date)
        times, values = self.process(raw_data, location, dataset)
        self.store(times, values, location, dataset)
        return times, values

    @abstractmethod
    def pull_all(self, start_date, end_date):
        pass

'''
MAX_LAT = 45.945248
MIN_LAT = 44.995300
MAX_LON = -100.286123
MIN_LON = -104.045343
'''

base = 'https://apps.sd.gov/NR92WQMAP/api/station/'
#url = 'https://arcgis.sd.gov/arcgis/rest/services/DENR/NR92_WQMAPPublic/MapServer/0/query?f=json&geometry=%7B%22spatialReference%22%3A%7B%22latestWkid%22%3A3857%2C%22wkid%22%3A102100%7D%2C%22xmin%22%3A-11271098.442818994%2C%22ymin%22%3A5322463.153554989%2C%22xmax%22%3A-10958012.374962993%2C%22ymax%22%3A5635549.22141099%7D&outFields=*&outSR=102100&spatialRel=esriSpatialRelIntersects&where=1%3D1&geometryType=esriGeometryEnvelope&inSR=102100'
#danr = requests.get(url)
#data = danr.json()
conn = sqlite3.connect('./Measurements.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS danr (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_ID TEXT NOT NULL,
    latitude FLOAT, 
    longitude FLOAT, 
    sampleDate DATETIME,
    pH FLOAT,
    tkn FLOAT,
    ammonia FLOAT,
    nitrateNitrite FLOAT,
    tp FLOAT,
    eColi FLOAT
)''')
print('Created stations table\n')

station_ids_in_range = list(station_ids.keys())

'''
for feature in data["features"]:
    longitude = feature["attributes"]["Longitude"]
    latitude = feature["attributes"]["Latitude"]

    if (MIN_LON <= longitude <= MAX_LON) and (MIN_LAT <= latitude <= MAX_LAT):
        station_ids_in_range.append(feature["attributes"]["StationID"])

print("StationIDs within the specified range:", station_ids_in_range)
'''

for stationid in station_ids_in_range:
    indv_url = base + stationid
    indv_stations = requests.get(indv_url).json()
    # indv_stations = pd.read_json(indv_stations)
    # indv_stations.fillna(None, inplace = True)
    lat = station_ids[stationid]['Latitude']
    lon = station_ids[stationid]['Longitude']

    for station in indv_stations['parameters']:
        date = station.get('sampleDate')
        if date:
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
        ph = station.get('pH')
        tkn = station.get('tkn')
        ammonia = station.get('ammonia')
        nitrate_nitrite = station.get('nitrateNitrite')
        tp = station.get('tp')
        eColi = station.get('eColi')
        #location = station_ids[stationid].get('LocationName', 'Unknown')
        data = {'station_ID': stationid, 'latitude': lat, 'longitude': lon, 'sampleDate': date,
                'pH': ph, 'tkn': tkn, 'ammonia': ammonia, 'nitrateNitrite': nitrate_nitrite, 'tp': tp, 'eColi': eColi}
        data_df = pd.DataFrame([data])


        for column in data_df.columns:
            if data_df[column].dtype == object:
                data_df[column] = data_df[column].replace("non-detect", None)
                data_df[column] = data_df[column].apply(
                    lambda x: "insignificant" if isinstance(x, str) and "<" in x else x)

        cursor.execute('''INSERT INTO danr (station_ID, latitude, longitude, 
        sampleDate, pH, tkn, ammonia, nitrateNitrite, tp, eColi) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
            
            (stationid, 
            lat, 
            lon, 
            date if date is not None else None,
            ph if ph is not None else None,
            tkn if tkn is not None else None,
            ammonia if ammonia is not None else None,
            nitrate_nitrite if nitrate_nitrite is not None else None,
            tp if tp is not None else None,
            eColi if eColi is not None else None)
        )
        print('Collected data from ' + stationid + '\n')

conn.commit()
conn.close()
