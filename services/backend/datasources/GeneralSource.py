#NOT IN USE
import requests

baseURLS = {"DANR" : "https://apps.sd.gov/NR92WQMAP/api/station/", "NDMES" : ""}
StationList = {"DANR" : ["SWLAZZZ2411A"]}

class DataSource():
    def __init__(self, source:str):
        self.source = source.upper()

    def _pull(self, start=None, end=None):
        if start != None and end !=None:
            self._pullBound(start, end)
        else:
            self._pullUnbound()

    def _pullUnbound(self):
        base = baseURLS.get(self.source)
        stations = StationList.get(self.source)

        for station in stations:
            data = requests.get(base+station).json()
        
        print(data)

    def _pullBound(self, start, end):
        pass
        

def main():
    test = DataSource("DANR")
    test._pull()

if (__name__ == "__main__"):
    main()



