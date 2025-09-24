from abc import ABC, abstractmethod
from datetime import datetime, date, timedelta
import os
import requests
from typing import Dict, List, Tuple, Any, Optional, Union
from .config import station_ids


class DataSource(ABC):
    def __init__(self, name, data_type):
        self.name = name
        self.data_type = data_type
        self.station_ids = station_ids

    @abstractmethod
    def fetch(self, location = None, dataset = None, start_date = None, end_date = None):
        

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
        from backend.database.sqlclasses import updateDictionary
        updateDictionary(times, values, location, dataset, self.data_type)

    def pull(self, location= None, dataset= None, start_date= None, end_date= None):
        """
        Main method to pull and store data from this source.
        """

        raw_data = self.fetch(location, dataset, start_date, end_date)
        times, values = self.process(raw_data, location, dataset)
        self.store(times, values, location, dataset)
        return times, values

    # @abstractmethod
    # def pull_all(self, start_date, end_date):
    #     pass

import json
import sqlite3
# import requests
from datetime import datetime
#import pandas as pd

station_ids = {
    "SWLAZZZ2411A": {"Latitude": 45.3486, "Longitude": -101.0942},
    "SWLAZZZ2411B": {"Latitude": 45.3477, "Longitude": -101.0921},
    "SWLAZZZ2411C": {"Latitude": 45.3468, "Longitude": -101.0904},
    "SWLAZZZ2411": {"Latitude": 45.3481, "Longitude": -101.0924},
    "SWLAZZZ2402B": {"Latitude": 45.415291, "Longitude": -100.972876},
    "SWLAZZZ2402": {"Latitude": 45.415296, "Longitude": -100.972884},
    "SWLAZZZ2402A": {"Latitude": 45.415415, "Longitude": -100.973195},
    "SWLAZZZ2402C": {"Latitude": 45.415123, "Longitude": -100.972563},
    "460945": {"Latitude": 45.657866, "Longitude": -100.817812},
    "460935": {"Latitude": 45.255906, "Longitude": -100.843161},
    "CAMPPOCP01": {"Latitude": 45.925788, "Longitude": -100.295418},
    "CITMONZ2417AA": {"Latitude": 45.435601, "Longitude": -101.065388},
    "FFLOaheMoreauRE": {"Latitude": 45.349815, "Longitude": -100.365792},
    "FFLittleMoreauL#1": {"Latitude": 45.348566, "Longitude": -101.093929},
    "FFLOaheGrandRE": {"Latitude": 45.606154, "Longitude": -100.529074},
    "FW08RSDP04R052": {"Latitude": 45.734775, "Longitude": -100.614753},
    "SWLAZZZ2013": {"Latitude": 45.480239, "Longitude": -100.746919},
    "SWLAZZZ2013A": {"Latitude": 45.480938, "Longitude": -100.749514},
    "SWLAZZZ2013B": {"Latitude": 45.479625, "Longitude": -100.746562},
    "SWLAZZZ2013C": {"Latitude": 45.481753, "Longitude": -100.742937},
    "SWLAZZZ2412A": {"Latitude": 45.356926, "Longitude": -101.084336},
    "SWLAZZZ2412B": {"Latitude": 45.355818, "Longitude": -101.083979},
    "SWLAZZZ2412C": {"Latitude": 45.354742, "Longitude": -101.084572},
    "SWLAZZZ2412": {"Latitude": 45.354747, "Longitude": -101.084616},
    "SWLAZZZ6302A": {"Latitude": 45.562368, "Longitude": -100.299956},
    "SWLAZZZ6302B": {"Latitude": 45.566762, "Longitude": -100.297363},
    "SWLAZZZ6302C": {"Latitude": 45.567166, "Longitude": -100.301773},
    "SWLAZZZ6302": {"Latitude": 45.563309, "Longitude": -100.299259},
    "SD_10096": {"Latitude": 45.655024, "Longitude": -101.040561},
    "SD_10100": {"Latitude": 45.337736, "Longitude": -100.373854},
    "SD_10697": {"Latitude": 45.514218, "Longitude": -100.508319},
    "SD_11901": {"Latitude": 45.676092, "Longitude": -100.786101},
    "SD_11903": {"Latitude": 45.680404, "Longitude": -101.074148},
    "SD_11904": {"Latitude": 45.173351, "Longitude": -101.145265},
    "SWLABAC2411": {"Latitude": 45.346947, "Longitude": -101.093815},
    "SWLAZZZ4913A": {"Latitude": 44.996341, "Longitude": -102.799566},
    "SWLAZZZ2410": {"Latitude": 45.020082, "Longitude": -101.458953},
    "SWLAZZZ2410A": {"Latitude": 45.021635, "Longitude": -101.458529},
    "SWLAZZZ2410B": {"Latitude": 45.017343, "Longitude": -101.458862},
    "SWLAZZZ2410C": {"Latitude": 45.014882, "Longitude": -101.459329},
    "SWLAZZZ4911A": {"Latitude": 45.032284, "Longitude": -102.607743},
    "SWLAZZZ4911B": {"Latitude": 45.031068, "Longitude": -102.607561},
    "SWLAZZZ4911C": {"Latitude": 45.031037, "Longitude": -102.610219},
    "SWLAZZZ4911": {"Latitude": 45.031162, "Longitude": -102.607627},
    "SWLAZZZ2408": {"Latitude": 45.4349, "Longitude": -101.4124},
    "SWLAZZZ2408A": {"Latitude": 45.4354, "Longitude": -101.4182},
    "SWLAZZZ2408B": {"Latitude": 45.4349, "Longitude": -101.4124},
    "SWLAZZZ2408C": {"Latitude": 45.4373, "Longitude": -101.4106},
    "GFPZZZ3502": {"Latitude": 45.6077, "Longitude": -103.6111},
    "SWLAZZZ5303": {"Latitude": 45.4182, "Longitude": -102.0967},
    "SWLAZZZ5303A": {"Latitude": 45.4219, "Longitude": -102.0977},
    "SWLAZZZ5303B": {"Latitude": 45.4182, "Longitude": -102.0967},
    "SWLAZZZ5303C": {"Latitude": 45.417, "Longitude": -102.0916},
    "SWLAZZZ5305": {"Latitude": 45.7767, "Longitude": -102.1742},
    "SWLAZZZ5305A": {"Latitude": 45.7772, "Longitude": -102.1805},
    "SWLAZZZ5305B": {"Latitude": 45.7767, "Longitude": -102.1742},
    "SWLAZZZ5305C": {"Latitude": 45.7779, "Longitude": -102.1686},
    "GFPZZZ5315": {"Latitude": 45.7499, "Longitude": -102.2055},
    "SWLAZZZ5315": {"Latitude": 45.7499, "Longitude": -102.2055},
    "SWLAZZZ5315A": {"Latitude": 45.721, "Longitude": -102.2683},
    "SWLAZZZ5315B": {"Latitude": 45.7499, "Longitude": -102.2055},
    "SWLAZZZ5315C": {"Latitude": 45.7636, "Longitude": -102.2534},
    "GFPZZZ5316": {"Latitude": 45.4418, "Longitude": -102.8969},
    "GRANDRZCROOKED": {"Latitude": 45.9075, "Longitude": -103.3769},
    "GRANDRZBULL": {"Latitude": 45.7428, "Longitude": -103.4274},
    "GRANDRZJONES": {"Latitude": 45.6874, "Longitude": -103.4838},
    "GRANDRZHORSE": {"Latitude": 45.6758, "Longitude": -103.1694},
    "GRANDRZBIGNASTY": {"Latitude": 45.6972, "Longitude": -102.8786},
    "GRANDRZLODGEPOL": {"Latitude": 45.7317, "Longitude": -102.3733},
    "GRANDRZBUTCHER": {"Latitude": 45.6306, "Longitude": -102.3379},
    "GRANDRZCLARKSFK": {"Latitude": 45.5573, "Longitude": -103.3624},
    "GRANDRZSRO05": {"Latitude": 45.7602, "Longitude": -102.1766},
    "GRANDRZNFG02": {"Latitude": 45.8021, "Longitude": -102.3622},
    "GRANDRZSFG08": {"Latitude": 45.6097, "Longitude": -102.4565},
    "GRANDRZSFG07": {"Latitude": 45.6489, "Longitude": -102.643},
    "GRANDRZNFG03": {"Latitude": 45.8837, "Longitude": -102.6523},
    "GRANDRZNFG01": {"Latitude": 45.9437, "Longitude": -102.9601},
    "GRANDRZSFG06": {"Latitude": 45.6398, "Longitude": -102.9973},
    "GRANDRZSFG04": {"Latitude": 45.5774, "Longitude": -103.5458},
    "SWLAZZZ3502A": {"Latitude": 45.611, "Longitude": -103.6154},
    "SWLAZZZ3502B": {"Latitude": 45.6066, "Longitude": -103.6096},
    "SWLAZZZ3502C": {"Latitude": 45.6041, "Longitude": -103.613},
    "SWLAZZZ3502": {"Latitude": 45.6066, "Longitude": -103.6096},
    "460955": {"Latitude": 45.548058, "Longitude": -103.972042},
    "460144": {"Latitude": 45.090172, "Longitude": -102.900356},
    "460143": {"Latitude": 45.208333, "Longitude": -101.507778},
    "460139": {"Latitude": 45.577903, "Longitude": -103.545586},
    "460678": {"Latitude": 45.610361, "Longitude": -102.454611},
    "460039": {"Latitude": 45.197778, "Longitude": -102.155556},
    "460640": {"Latitude": 45.760533, "Longitude": -102.176925},
    "460147": {"Latitude": 45.376697, "Longitude": -102.173619},
    "460138": {"Latitude": 45.687679, "Longitude": -101.340067},
    "460677": {"Latitude": 45.802143, "Longitude": -102.362378},
    "460160": {"Latitude": 45.907641, "Longitude": -103.377066},
    "460161": {"Latitude": 45.743304, "Longitude": -103.427802},
    "460162": {"Latitude": 45.639835, "Longitude": -102.997773},
    "SWLAZZZ5313A": {"Latitude": 45.468476, "Longitude": -102.406794},
    "SWLAZZZ5313C": {"Latitude": 45.462129, "Longitude": -102.399202},
    "SWLAZZZ5313B": {"Latitude": 45.466205, "Longitude": -102.402291},
    "SWLAZZZ5313": {"Latitude": 45.466212, "Longitude": -102.402054},
    "SWLAZZZ2409A": {"Latitude": 45.250634, "Longitude": -101.465701},
    "SWLAZZZ2409B": {"Latitude": 45.248802, "Longitude": -101.465789},
    "SWLAZZZ2409C": {"Latitude": 45.24693, "Longitude": -101.465876},
    "SWLAZZZ2409": {"Latitude": 45.2487, "Longitude": -101.465952},
    "SHDHILL1A": {"Latitude": 45.60992, "Longitude": -102.456761},
    "SHDHILL1B": {"Latitude": 45.648874, "Longitude": -102.643432},
    "SHDHILL1C": {"Latitude": 45.654403, "Longitude": -102.888957},
    "FFCoalSp": {"Latitude": 45.421545, "Longitude": -102.099},
    "FFLIsabel": {"Latitude": 45.436516, "Longitude": -101.422147},
    "FFLittleMissouriR": {"Latitude": 45.547004, "Longitude": -103.970775},
    "FFShadehillR": {"Latitude": 45.749838, "Longitude": -102.221562},
    "FFPudwellD": {"Latitude": 45.925545, "Longitude": -101.272629},
    "LIMIRV01": {"Latitude": 45.517139, "Longitude": -103.988324},
    "LIMIRV02": {"Latitude": 45.775489, "Longitude": -103.886982},
    "FW08SD056": {"Latitude": 45.516826, "Longitude": -104.011887},
    "SWLAZZZ5301": {"Latitude": 45.677401, "Longitude": -102.175784},
    "SWLAZZZ5301A": {"Latitude": 45.677287, "Longitude": -102.175921},
    "SWLAZZZ5301B": {"Latitude": 45.677576, "Longitude": -102.175464},
    "SWLAZZZ5301C": {"Latitude": 45.677648, "Longitude": -102.174706},
    "460193": {"Latitude": 45.21772, "Longitude": -102.179788},
    "SWLAZZZ5319A": {"Latitude": 45.602048, "Longitude": -102.467979},
    "SWLAZZZ5319B": {"Latitude": 45.602438, "Longitude": -102.466739},
    "SWLAZZZ5319C": {"Latitude": 45.602869, "Longitude": -102.466002},
    "SWLAZZZ5319": {"Latitude": 45.602419, "Longitude": -102.466908},
    "SWLAZZZ2006A": {"Latitude": 45.922234, "Longitude": -101.341493},
    "SWLAZZZ2006B": {"Latitude": 45.923926, "Longitude": -101.338481},
    "SWLAZZZ2006C": {"Latitude": 45.922657, "Longitude": -101.337996},
    "SWLAZZZ2006": {"Latitude": 45.923087, "Longitude": -101.339531},
    "SD_10014": {"Latitude": 45.155092, "Longitude": -102.752593},
    "SD_10027": {"Latitude": 45.915118, "Longitude": -103.019619},
    "SD_10037": {"Latitude": 45.878237, "Longitude": -102.635177},
    "SD_10039": {"Latitude": 45.59689, "Longitude": -103.927461},
    "SD_11295": {"Latitude": 45.353698, "Longitude": -102.524606},
    "SD_11299": {"Latitude": 45.565251, "Longitude": -101.760961},
    "SD_11896": {"Latitude": 45.156512, "Longitude": -102.496494},
    "SD_11905": {"Latitude": 45.1593, "Longitude": -102.782132},
    "FFFlatCreekL": {"Latitude": 45.778191, "Longitude": -102.180196},
    "SWLABAC5315": {"Latitude": 45.757192, "Longitude": -102.215908},
    "SWLABAC3502": {"Latitude": 45.605338, "Longitude": -103.609042},
    "FFGardnerL": {"Latitude": 45.6089, "Longitude": -103.611},
    "SWLABAC2408": {"Latitude": 45.436494, "Longitude": -101.41755},
    "SWLABAC5303": {"Latitude": 45.416567, "Longitude": -102.095125},
    "SWLABAC5309": {"Latitude": 45.774778, "Longitude": -102.020567},
    "SWLAZZZ5309": {"Latitude": 45.776065, "Longitude": -102.017108},
    "SWLAZZZ5309B": {"Latitude": 45.776065, "Longitude": -102.017108},
    "SWLAZZZ5309A": {"Latitude": 45.778032, "Longitude": -102.020174},
    "SWLAZZZ5309C": {"Latitude": 45.77872, "Longitude": -102.011738},
    "SWLABAC5305": {"Latitude": 45.775844, "Longitude": -102.175777},
    "SWLABAC2010": {"Latitude": 45.921796, "Longitude": -101.2663},
    "SWLAZZZ2010": {"Latitude": 45.923232, "Longitude": -101.26662},
    "SWLAZZZ2010B": {"Latitude": 45.923232, "Longitude": -101.26662},
    "SWLAZZZ2010A": {"Latitude": 45.925165, "Longitude": -101.271997},
    "SWLAZZZ2010C": {"Latitude": 45.926006, "Longitude": -101.265862},
}
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
print('Created staitons table\n')

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
<<<<<<< Updated upstream
        
=======

        data = {'location': location, 'station_ID': stationid, 'latitude': lat, 'longitude': lon, 'sampleDate': date,
                'pH': ph, 'tkn': tkn, 'ammonia': ammonia, 'nitrateNitrite': nitrate_nitrite, 'tp': tp, 'eColi': eColi}
        data_df = pd.DataFrame(data)


        for column in data_df.columns:
            if data_df[column].dtype == object:
                data_df[column] = data_df[column].replace("non-detect", None)
                data_df[column] = data_df[column].apply(
                    lambda x: "insignificant" if isinstance(x, str) and "<" in x else x)

>>>>>>> Stashed changes
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
