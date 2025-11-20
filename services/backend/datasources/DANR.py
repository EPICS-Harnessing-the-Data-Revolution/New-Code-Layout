import requests
from base2 import DataSource
import json
from datetime import datetime
import pandas as pd
import sqlite3

baseURLS = {"DANR" : "https://apps.sd.gov/NR92WQMAP/api/station/", "NDMES" : ""}
StationList = {"DANR" : ["SWLAZZZ2411A", "CAMPPOCP01", "SD_11904"]}

class DANR(DataSource):
    def __init__(self, start_date=None, format=None):
        super().__init__("DANR", start_date, format)
        self.URL = baseURLS.get(self.source)
        self.stations = StationList.get(self.source)
    
    def _pull(self):
        data = []
        for station in self.stations:
            data.append(requests.get(self.URL+station).json())
        self.data = data

    
    def _process(self):
        format_string = "%Y-%m-%dT%H:%M:%S"
        count = 0

        for station_index, station in enumerate(self.data):
            for sample in station['parameters']:           
                EpochTime = datetime.strptime(sample['sampleDate'], format_string)
                if EpochTime<=self.cutoff:
                    count +=1


        del self.data[station_index]['parameters'][:count]
    
    def _push(self):
        conn = sqlite3.connect('mydatabase.db')
        db = pd.DataFrame()
        for data in self.data:

            meta = [['station', key] for key in list(data['station'].keys())]
            temp = pd.json_normalize(data=data, record_path= 'parameters', meta=meta)
            db = pd.concat([db, temp])

        db.to_sql('mydatabase.db', conn, if_exists='replace', index=False)

        print(db)

        conn.close()

    
def main():
    test = DANR("2025-8-01 0:0:0", "%Y-%m-%d %H:%M:%S")
    test._pull()
    test._process()
    test._push()

if (__name__ == "__main__"):
    main()
    
