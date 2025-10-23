import requests
from services.backend.datasources.base import DataSource
from services.backend.datasources.utils import DataParser
from services.backend.datasources.utils import DateHelper
from services.backend.datasources.config import SHADEHILL_DATASETS
import sqlite3
from services.backend.database.sqlclaases import SQL_CONVERSION

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

        lines = raw_data.splitlines()
        
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
        Pull data for all datasets and store them together to avoid overwriting.
        """
        print("Pulling Shadehill data...")
        
        # Collect all datasets first
        all_data = {}  # {timestamp: {dataset_name: value}}
        
        for dataset_code, dataset_name in self.datasets.items():
            try:
                print(f"  Fetching {dataset_name}...")

                raw_data = self.fetch("Shadehill", dataset_code, start_date, end_date)
                
                if raw_data:
                    times, values = self.process(raw_data, "Shadehill", dataset_code)
                    if times and values:
                        # Store in our collection
                        for time, value in zip(times, values):
                            if time not in all_data:
                                all_data[time] = {}
                            all_data[time][dataset_name] = value
            except Exception as e:
                print(f"Error processing Shadehill data for {dataset_name}: {e}")
        
        # Now store all datasets together
        if all_data:
            print(f"  Storing {len(all_data)} records with all datasets...")
            self.store_all_datasets(all_data, "Shadehill")
    
    def store_all_datasets(self, all_data, location):
        """
        Store all datasets for each timestamp in a single database operation.
        Uses a custom approach to avoid overwriting data.
        """
        
        # Use direct database connection instead of _get_db_connection
        conn = None
        try:
            conn = sqlite3.connect('./Measurements.db')
            cursor = conn.cursor()
            
            # Get all unique timestamps
            timestamps = sorted(all_data.keys())
            
            for timestamp in timestamps:
                datasets = all_data[timestamp]
                
                # Check if record already exists
                cursor.execute("SELECT * FROM shadehill WHERE location = ? AND datetime = ?", (location, timestamp))
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # Update existing record with new values
                    update_fields = []
                    update_values = []
                    
                    for dataset_name, value in datasets.items():
                        if value is not None:
                            sql_field = SQL_CONVERSION.get(dataset_name)
                            if sql_field:
                                update_fields.append(f"{sql_field} = ?")
                                update_values.append(value)
                    
                    if update_fields:
                        update_values.append(location)
                        update_values.append(timestamp)
                        sql = f"UPDATE shadehill SET {', '.join(update_fields)} WHERE location = ? AND datetime = ?"
                        cursor.execute(sql, update_values)
                else:
                    # Insert new record with all values
                    fields = ['location', 'datetime']
                    values = [location, timestamp]
                    placeholders = ['?', '?']
                    
                    for dataset_name, value in datasets.items():
                        if value is not None:
                            sql_field = SQL_CONVERSION.get(dataset_name)
                            if sql_field:
                                fields.append(sql_field)
                                values.append(value)
                                placeholders.append('?')
                    
                    if len(fields) > 2:  # More than just location and datetime
                        sql = f"INSERT INTO shadehill ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
                        cursor.execute(sql, values)
            
            conn.commit()
            print(f"Successfully stored {len(timestamps)} records with all datasets")
            
        except Exception as e:
            print(f"Error storing datasets: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

#TESTING
shadehill = ShadehillDataSource()
print(DateHelper.string_to_list("20210624"))
print((shadehill.fetch("Shadehill",dataset="AF", start_date=DateHelper.string_to_list("20210624"), end_date=DateHelper.string_to_list("20240401"))))
