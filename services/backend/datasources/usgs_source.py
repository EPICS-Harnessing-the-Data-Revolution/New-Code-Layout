import requests
import csv
import os
from services.backend.datasources.base import DataSource
from services.backend.datasources.utils import DataParser

class USGSDataSource(DataSource):
    """
    Data source for USGS gauge data.
    """
    
    def __init__(self):
        super().__init__("USGS", "gauge")
        self.location_dict = {
            'Hazen': ['06340500', 1],
            'Stanton': ['06340700', 2],
            'Washburn': ['06341000', 2],
            'Price': ['06342020', 2],
            'Bismarck': ['06342500', 3],
            'Schmidt': ['06349700', 2],
            'Judson': ['06348300', 1], 
            'Mandan': ['06349000', 1],
            'Breien': ['06354000', 1]   ,
            'Wakpala': ['06354881', 4],
            'Little Eagle': ['06357800', 4],
            'Cash': ['06356500', 4],
            'Whitehorse': ['06360500', 4]
        }
        
    def fetch(self, location, dataset, start_date, end_date):
        location_data = self.location_dict[location]
        code = location_data[0]
        category = location_data[1]
        
        s_year, s_month, s_day = start_date['year'], start_date['month'], start_date['day']
        e_year, e_month, e_day = end_date['year'], end_date['month'], end_date['day']

        if category == 1:
            url = f'https://waterdata.usgs.gov/nwis/uv?cb_00060=on&cb_00065=on&cb_63160=on&format=rdb&site_no={code}&legacy=1&period=&begin_date={s_year}-{s_month}-{s_day}&end_date={e_year}-{e_month}-{e_day}'
            num_sets = 3
            linecount = 56
        elif category == 2:
            url = f'https://waterdata.usgs.gov/nwis/uv?cb_00065=on&cb_63160=on&format=rdb&site_no={code}&legacy=1&period=&begin_date={s_year}-{s_month}-{s_day}&end_date={e_year}-{e_month}-{e_day}'
            num_sets = 2
            linecount = 54
        elif category == 3:
            url = f'https://waterdata.usgs.gov/nwis/uv?cb_00010=on&cb_00060=on&cb_00065=on&cb_63160=on&format=rdb&site_no={code}&legacy=1&period=&begin_date={s_year}-{s_month}-{s_day}&end_date={e_year}-{e_month}-{e_day}'
            num_sets = 4
            linecount = 58
        elif category == 4:
            url = f'https://waterdata.usgs.gov/nwis/uv?cb_00060=on&cb_00065=on&format=rdb&site_no={code}&legacy=1&period=&begin_date={s_year}-{s_month}-{s_day}&end_date={e_year}-{e_month}-{e_day}'
            num_sets = 2
            linecount = 54
         
        linecount2 = linecount + 3

        response = requests.get(url)

        file_name = f"./temp_{location}"
        data_file = f"./temp_data.txt"

        with open(data_file, "w") as f:
            writer = csv.writer(f)
            for line in response.text.split("\n"):
                writer.writerow(line.split("\t"))
        
        data = []
        count = 0
        alternate = 0
        
        with open(data_file, "r") as file:
            for line in file:
                if count == linecount:
                    data.append(line)
                elif count > linecount2:
                    if alternate % 2 == 0:
                        line = line.strip('\n')
                        data.append(line)
                    alternate += 1
                count += 1
        
        
        with open(f"{file_name}.csv", "w") as file:
            for line in data:
                file.write(f"{line}")
        
        data_matrix = []
        with open(f"{file_name}.csv", 'rt') as f:
            reader = csv.reader(f)
            data_matrix = list(reader)
        
        
        try:
            os.remove(f"{file_name}.csv")
            os.remove(data_file)
        except Exception as e:
            print(f"Error removing temporary files: {e}")
        
        
        return {
            'data_matrix': data_matrix[:-1],  
            'category': category,
            'num_sets': num_sets
        }
    
    def process(self, raw_data, location, dataset):
        """
        Process the raw USGS data.
        
        Args:
            raw_data: Raw data dictionary
            location: Location the data is for
            dataset: Type of data (e.g., "Gauge Height")
            
        Returns:
            Tuple of (times, values)
        """
        if not raw_data or 'data_matrix' not in raw_data:
            return [], []
            
        data_matrix = raw_data['data_matrix']
        category = raw_data['category']
        num_sets = raw_data['num_sets']
        
        if num_sets == 2:
            length = 8  
        elif num_sets == 3:  
            length = 10
        elif num_sets == 4:
            length = 12
        
        times = []
        dataset1 = []
        dataset2 = []
        dataset3 = []
        dataset4 = []
        
        for matrixindex in range(4, len(data_matrix)):
            if matrixindex != 0:
                try:
                    for data in range(0, length):
                        if data == 2:
                            times.append(data_matrix[matrixindex][data])
                        elif data == 4:
                            dataset1.append(data_matrix[matrixindex][data])
                        elif data == 6:
                            dataset2.append(data_matrix[matrixindex][data])
                        elif num_sets >= 3 and data == 8:
                            dataset3.append(data_matrix[matrixindex][data])
                        elif num_sets == 4 and data == 10:
                            dataset4.append(data_matrix[matrixindex][data])
                except IndexError:
                    
                    continue
        
        
        datasets = {}
        
        if category == 1:
            datasets = {
                "Elevation": dataset1,
                "Discharge": dataset2,
                "Gauge Height": dataset3
            }
            
            if location == 'Judson':
                datasets = {
                    "Elevation": dataset1,
                    "Gauge Height": dataset2,
                    "Discharge": dataset3
                }
        elif category == 2:
            datasets = {
                "Elevation": dataset1,
                "Gauge Height": dataset2
            }
        elif category == 3:
            datasets = {
                "Elevation": dataset1,
                "Water Temperature": dataset2,
                "Discharge": dataset3,
                "Gauge Height": dataset4
            }
        elif category == 4:
            datasets = {
                "Discharge": dataset1,
                "Gauge Height": dataset2
            }
        
        
        if "Discharge" in datasets:
            discharge = datasets["Discharge"]
            for i in range(0, len(discharge)):
                if discharge[i] == 'Ice':
                    discharge[i] = 0
        
        
        if dataset in datasets:
            values = datasets[dataset]
            
            values = DataParser.parse_numeric_list(values)
            return times, values
        else:
            return [], []
    
    def pull_all(self, start_date, end_date):
        """
        Pull data for all locations and datasets.
        """
        datasets = ["Gauge Height", "Elevation", "Discharge", "Water Temperature"]
        
        for location in self.location_dict.keys():
            print(f"Pulling USGS data for {location}...")
            
            try:
                
                raw_data = self.fetch(location, None, start_date, end_date)
                
                
                for dataset in datasets:
                    times, values = self.process(raw_data, location, dataset)
                    if times and values:
                        self.store(times, values, location, dataset)
            except Exception as e:
                print(f"Error processing USGS data for {location}: {e}")