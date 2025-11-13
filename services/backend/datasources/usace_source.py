import requests
import csv
import os
import ssl
import urllib3
from datetime import datetime

from services.backend.datasources.base2 import DataSource
from services.backend.datasources.utils import DataParser
from services.backend.sqlclasses import updateDictionary

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class USACEDataSource(DataSource):
    """
    Data source for USACE dam data using base2 template.
    """
    
    def __init__(self, start_date=None, format=None):
        super().__init__("USACE", start_date, format)
        self.location_dict = {
            'Fort Peck': ['FTPK'],
            'Garrison': ['GARR'],
            'Oahe': ['OAHE'],
            'Big Bend': ['BEND'],
            'Fort Randall': ['FTRA'],
            'Gavins Point': ['GAPT']
        }
        self.data = []  # Store raw data from _pull
        self.processed = []  # Store processed data from _process
        
        # Dataset names
        self.datasets = [
            "Elevation", "Flow Spill", "Flow Powerhouse", "Flow Out", 
            "Tailwater Elevation", "Energy", "Water Temperature", "Air Temperature"
        ]
        
    def _pull(self):
        """
        Pull raw USACE data for all configured locations.
        Stores raw data in self.data.
        """
        self.data = []
        
        for location, location_data in self.location_dict.items():
            location_code = location_data[0]
            url = f'https://www.nwd-mr.usace.army.mil/rcc/programs/data/{location_code}'
            
            try:
                # First try with requests
                response = requests.get(url, verify=False, timeout=30)
                response.raise_for_status()
            except (requests.exceptions.RequestException, requests.exceptions.SSLError) as e:
                # If requests fails due to SSL, use curl via subprocess as fallback
                try:
                    import subprocess
                    result = subprocess.run(
                        ['curl', '-k', '-s', '--max-time', '30', url],
                        capture_output=True,
                        text=True,
                        timeout=35,
                        check=False
                    )
                    if result.returncode == 0 and result.stdout:
                        # Create a mock response object compatible with requests
                        class MockResponse:
                            def __init__(self, data, status_code):
                                self.text = data
                                self.status_code = status_code
                            def raise_for_status(self):
                                if self.status_code != 200:
                                    raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")
                        response = MockResponse(result.stdout, 200)
                    else:
                        raise requests.exceptions.HTTPError(f"curl returned code {result.returncode}")
                except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e2:
                    print(f"Error fetching USACE data for {location}: {e} (curl fallback also failed: {e2})")
                    self.data.append({
                        'location': location,
                        'raw': None
                    })
                    continue
                except Exception as e2:
                    print(f"Error fetching USACE data for {location}: {e} (curl fallback also failed: {e2})")
                    self.data.append({
                        'location': location,
                        'raw': None
                    })
                    continue
            
            # Create temporary file
            file_name = f"./temp_{location}.txt"
            
            # Write response to file
            with open(file_name, "w") as f:
                writer = csv.writer(f)
                for line in response.text.split("\n"):
                    writer.writerow(line.split("\t"))
            
            # Extract relevant data
            count = 0
            alternate = 0
            data = []
            
            with open(file_name, "r") as file:
                for line in file:
                    if count == 4:
                        data.append(line)
                    elif count > 5:
                        if alternate % 2 == 0:
                            data.append(line.strip('"'))
                        alternate += 1
                    count += 1
            
            # Rewrite the file with cleaned data
            with open(file_name, "w") as file:
                for line in data:
                    file.write(f"{line}")
            
            # Read the file content
            file_content = ""
            with open(file_name, "r") as file:
                file_content = file.read()
            
            # Clean up
            try:
                os.remove(file_name)
            except Exception as e:
                print(f"Error removing temporary file: {e}")
            
            self.data.append({
                'location': location,
                'raw': file_content
            })
    
    def _process(self):
        """
        Process raw USACE data in self.data into standardized series.
        Stores series in self.processed.
        """
        self.processed = []
        
        for entry in self.data:
            raw_data = entry.get('raw')
            location = entry.get('location')
            
            if not raw_data:
                continue
            
            # Parse the raw data
            lines = raw_data.strip().split('\n')
            
            Date = []
            Hour = []
            Elevation = []
            Flow_Spill = []
            Flow_Powerhouse = []
            Flow_Out = []
            Elev_Tailwater = []
            Energy = []
            Temp_Water = []
            Temp_Air = []
            
            for i, line in enumerate(lines):
                if i > 1 and i < 170:  # Skip header and limit data
                    parts = line.split()
                    if len(parts) >= 10:  # Ensure line has enough columns
                        Date.append(parts[0])
                        Hour.append(parts[1])
                        Elevation.append(parts[2])
                        Flow_Spill.append(parts[3])
                        Flow_Powerhouse.append(parts[4])
                        Flow_Out.append(parts[5])
                        Elev_Tailwater.append(parts[6])
                        Energy.append(parts[7])
                        Temp_Water.append(parts[8])
                        Temp_Air.append(parts[9])
            
            # Parse numeric values
            Elevation = DataParser.parse_numeric_list(Elevation)
            Flow_Spill = DataParser.parse_numeric_list(Flow_Spill)
            Flow_Powerhouse = DataParser.parse_numeric_list(Flow_Powerhouse)
            Flow_Out = DataParser.parse_numeric_list(Flow_Out)
            Elev_Tailwater = DataParser.parse_numeric_list(Elev_Tailwater)
            Energy = DataParser.parse_numeric_list(Energy)
            Temp_Water = DataParser.parse_numeric_list(Temp_Water)
            Temp_Air = DataParser.parse_numeric_list(Temp_Air)
            
            # Combine date and time and apply cutoff filter
            times_all = []
            for i in range(len(Hour)):
                time_str = Date[i] + " " + Hour[i]
                # Convert to standard format and apply cutoff filter
                try:
                    # Parse the time string (format may vary)
                    dt_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    formatted_time = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        dt_obj = datetime.strptime(time_str, "%Y/%m/%d %H:%M")
                        formatted_time = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        formatted_time = time_str
                
                # Apply cutoff filter
                if isinstance(self.cutoff, datetime):
                    try:
                        if datetime.strptime(formatted_time, "%Y-%m-%d %H:%M:%S") <= self.cutoff:
                            times_all.append(None)
                            continue
                    except Exception:
                        pass
                times_all.append(formatted_time)
            
            # Map datasets to their values
            datasets = {
                "Elevation": Elevation,
                "Flow Spill": Flow_Spill,
                "Flow Powerhouse": Flow_Powerhouse,
                "Flow Out": Flow_Out,
                "Tailwater Elevation": Elev_Tailwater,
                "Energy": Energy,
                "Water Temperature": Temp_Water,
                "Air Temperature": Temp_Air
            }
            
            # Create processed series for each dataset
            for dataset_name, values in datasets.items():
                times = []
                filtered_values = []
                for i, t in enumerate(times_all):
                    if t is not None and i < len(values) and values[i] is not None:
                        times.append(t)
                        filtered_values.append(values[i])
                
                if times and filtered_values:
                    self.processed.append({
                        'location': location,
                        'dataset': dataset_name,
                        'times': times,
                        'values': filtered_values,
                    })
    
    def _push(self):
        """
        Push processed series into SQL using updateDictionary for 'dam' table.
        """
        for series in self.processed:
            times = series.get('times') or []
            values = series.get('values') or []
            location = series.get('location')
            dataset = series.get('dataset')
            if times and values:
                updateDictionary(times, values, location, dataset, 'dam')
    
    def pull_all(self, start_date, end_date):
        """
        Pull all relevant data for this source for the given date range.
        This method is for compatibility with the DataSourceManager.
        
        Args:
            start_date: Start date dictionary with year, month, day OR datetime object
            end_date: End date dictionary with year, month, day OR datetime object
        """
        # Convert date dictionaries to format expected by base2
        if isinstance(start_date, dict):
            # DateHelper returns strings, so convert to int then format
            year = int(start_date['year'])
            month = int(start_date['month'])
            day = int(start_date['day'])
            start_date_str = f"{year}{month:02d}{day:02d}"
            date_format = "%Y%m%d"
        elif isinstance(start_date, datetime):
            start_date_str = start_date.strftime("%Y%m%d")
            date_format = "%Y%m%d"
        else:
            # If already a string, try to parse it
            start_date_str = str(start_date)
            date_format = "%Y%m%d"
        
        # Set the cutoff for date filtering in _pull
        if start_date_str and date_format:
            try:
                self.cutoff = datetime.strptime(start_date_str, date_format)
            except ValueError:
                self.cutoff = None
        else:
            self.cutoff = None
        
        # Call update which will use _pull, _process, _push
        self.update()
