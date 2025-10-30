import requests
from base2 import DataSource
import json
from datetime import datetime

baseURLS = {"DANR" : "https://apps.sd.gov/NR92WQMAP/api/station/", "NDMES" : ""}
StationList = {"DANR" : ["SWLAZZZ2411A"]}

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

        """for station in self.data:
            for sample in station['parameters']:
                
                EpochTime = datetime.strptime(sample['sampleDate'], format_string)
                if EpochTime<=self.cutoff:
                    pass"""

        self.data = [sample for sample in self.data[0]['parameters'] if datetime.strptime(sample['sampleDate'], format_string)>self.cutoff]
        print(json.dumps(self.data, indent=4))

        return super()._process()
    
    def _push(self):
        return super()._push()
    
def main():
    test = DANR("2025-8-01 0:0:0", "%Y-%m-%d %H:%M:%S")
    test._pull()
    test._process()

if (__name__ == "__main__"):
    main()
    
