import requests
from services.backend.datasources.base import DataSource
from services.backend.datasources.utils import DataParser
from services.backend.datasources.utils import DateHelper
from services.backend.datasources.config import SHADEHILL_DATASETS

class ShadehillDataSource(DataSource):
    """
    Data source for Shadehill reservoir data.
    """
    
    def __init__(self):
        super().__init__("Shadehill", "shadehill")
        self.datasets = SHADEHILL_DATASETS
        
    def fetch(self, location, dataset = None, start_date = None, end_date = None):
        """
        Fetch data from Shadehill API.
        """
        # URL for the form action
        url = "https://www.usbr.gov/gp-bin/arcread.pl"



        # Form data to be submitted
        form_data = {
            'st': 'SHR',
            'by': start_date['year'],
            'bm': start_date['month'],
            'bd': start_date['day'],
            'ey': end_date['year'],
            'em': end_date['month'],
            'ed': end_date['day'],
            'pa': dataset,
        }
        print(form_data)
        
        try:
            print(url)
            response = requests.post(url, data=form_data)
            
            if response.status_code != 200:
                print(f"Error fetching Shadehill data for {dataset}: HTTP {response.status_code}")
                return None
                
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Shadehill data for {dataset}: {e}")
            return None
    
    def process(self, raw_data, location, dataset):
        """
        Process the raw Shadehill data.
        """
        if not raw_data:
            return [], []

        dataset_code = dataset
        if dataset in self.datasets.values():
            for code, name in self.datasets.items():
                if name == dataset:
                    dataset_code = code
                    break

        lines = raw_data.strip().split('\r')
        
        times = []
        values = []

        for i, line in enumerate(lines):
            if i >= 3:
                parts = line.split(" ")
                if len(parts) >= 2:

                    date_parts = parts[0].strip("\n").split("/")
                    if len(date_parts) == 3:
                        year = date_parts[0]
                        month = date_parts[1]
                        day = date_parts[2]

                        timestamp = f"{year}-{month}-{day} 00:00"
                        times.append(timestamp)

                        try:
                            value = float(parts[-1])

                            if value > 900000:
                                values.append(None)
                            else:
                                values.append(value)
                        except:
                            values.append(None)

        if times and values and len(times) > len(values):
            times.pop()
        elif times and values and len(values) > len(times):
            values.pop()
        
        return times, values
    
    def pull_all(self, start_date, end_date):
        """
        Pull data for all datasets.
        """
        print("Pulling Shadehill data...")
        
        for dataset_code, dataset_name in self.datasets.items():
            try:
                print(f"  Fetching {dataset_name}...")

                raw_data = self.fetch("Shadehill", dataset_code, start_date, end_date)
                
                if raw_data:
                    times, values = self.process(raw_data, "Shadehill", dataset_code)
                    if times and values:
                        self.store(times, values, "Shadehill", dataset_name)
            except Exception as e:
                print(f"Error processing Shadehill data for {dataset_name}: {e}")

#TESTING
shadehill = ShadehillDataSource()
print(DateHelper.string_to_list("20210624"))
print((shadehill.fetch("Shadehill",dataset="AF", start_date=DateHelper.string_to_list("20210624"), end_date=DateHelper.string_to_list("20230401"))))
