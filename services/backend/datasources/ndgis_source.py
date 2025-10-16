# ndgis_source.py
from abc import ABC, abstractmethod
from datetime import datetime, date, timedelta
import os
import requests
from typing import Dict, List, Tuple, Any, Optional, Union
import pandas as pd
import io
from base import DataSource  # Import the base class
# from services.backend.datasources.utils import DataParser # Not directly used in your original pullNDGIS
# from services.backend.datasources.utils import DateHelper # Not directly used in your original pullNDGIS


class NDGISWaterChem(DataSource):
    def __init__(self, name="NDGIS Water Chemistry", data_type="water_quality"):
        super().__init__(name, data_type)
        self.masterlist_path = r'INSERT THE PATH TO THE MASTERLIST HERE'  # Path to your Excel masterlist

    def _discover_station_ids_arcgis(self):
        """
        Discover all available station IDs from NDGIS ArcGIS REST API as a fallback
        when no masterlist is provided. Returns a list of station id strings.
        """
        try:
            base_url = (
                "https://ndgishub.nd.gov/arcgis/rest/services/Applications/DOH_SurfaceWaterSamplingSites/MapServer/0/query"
            )
            station_ids = []
            result_offset = 0
            page_size = 2000
            while True:
                params = {
                    "where": "1=1",
                    "outFields": "Site_ID",
                    "returnGeometry": "false",
                    "f": "json",
                    "resultOffset": result_offset,
                    "resultRecordCount": page_size,
                }
                resp = requests.get(base_url, params=params, timeout=30)
                resp.raise_for_status()
                payload = resp.json()
                features = payload.get("features", [])
                if not features:
                    break
                for feat in features:
                    attrs = feat.get("attributes", {})
                    sid = attrs.get("Site_ID")
                    if sid is not None and str(sid).strip():
                        station_ids.append(str(sid).strip())
                # Stop if returned less than a full page
                if len(features) < page_size:
                    break
                result_offset += page_size
            # Deduplicate while preserving order
            seen = set()
            unique_ids = []
            for sid in station_ids:
                if sid not in seen:
                    seen.add(sid)
                    unique_ids.append(sid)
            return unique_ids
        except Exception as e:
            print(f"Error discovering station IDs from ArcGIS: {e}")
            return []

    def _get_dataset_name(self, url):
        """Sends a POST request and gets the response text (dataset name)."""
        response = requests.post(url)
        if response.status_code == 200 and response.text:
            return response.text.replace('"', '')  # Remove quotes from dataset name
        else:
            print(f"Error: Unable to fetch dataset name from {url}. Status code: {response.status_code}")
            return None

    def fetch(self, location=None, dataset=None, start_date=None, end_date=None):
        """
        Fetches water chemical data for specified station IDs and chemicals.

        Args:
            location (list, optional): A list of station IDs to fetch data for. Defaults to None (fetches all from masterlist).
            dataset (list, optional): A list of water chemical parameters to fetch. Defaults to a predefined list.
            start_date (datetime.date, optional): Not used in this implementation. Defaults to None.
            end_date (datetime.date, optional): Not used in this implementation. Defaults to None.

        Returns:
            dict: A dictionary where keys are station IDs and values are dictionaries of
                  chemical parameters and their corresponding DataFrames. Returns None on error.
        """
        station_ids = []
        if location:
            station_ids = location
        else:
            # Try masterlist first
            loaded_from_master = False
            try:
                if self.masterlist_path and os.path.exists(self.masterlist_path):
                    df = pd.read_excel(self.masterlist_path)
                    if not df.empty:
                        station_ids = df.iloc[:, 0].astype(str).tolist()
                        loaded_from_master = True
                    else:
                        print(f"Warning: No station IDs found in the masterlist at {self.masterlist_path}")
            except Exception as e:
                print(f"Warning: Could not read masterlist '{self.masterlist_path}': {e}")

            # Fallback to ArcGIS discovery if masterlist not available or empty
            if not loaded_from_master or not station_ids:
                print("Discovering station IDs from NDGIS ArcGIS...")
                station_ids = self._discover_station_ids_arcgis()
                if not station_ids:
                    print("Error: Unable to discover any station IDs from ArcGIS.")
                    return None

        water_chemicals = dataset if dataset else [
            'Phosphorus (Total) (P)', 'Phosphorus (Total Kjeldahl) (P)', 'Nitrate + Nitrite (N)',
            'Nitrate Forms Check', 'Nitrate + Nitrite (N) Dis', 'Nitrogen (Total Kjeldahl)',
            'Nitrogen (TKN-Dissolved)',
            'Nitrogen (Total-Dis)', 'E.coli', 'Nitrogen (Total)', 'pH', 'Ammonia (N)', 'Ammonia (N)-Dissolved',
            'Ammonia Forms Check', 'Diss Ammonia TKN Check', 'Dissolved Phosphorus as P'
        ]

        all_station_data = {}
        for station_id in station_ids:
            print(f"Fetching data for station ID: {station_id}")
            waterchem_url = f"https://deq.nd.gov/Webservices_SWDataApp/DownloadStationsData/GetStationsWaterChemData/{station_id}"
            waterchem_dataset_name = self._get_dataset_name(waterchem_url)

            if waterchem_dataset_name:
                waterchem_data_url = f"https://deq.nd.gov/WQ/3_Watershed_Mgmt/SWDataApp/downloaddata/{waterchem_dataset_name}.csv"
                try:
                    response = requests.get(waterchem_data_url)
                    response.raise_for_status()  # Raise an exception for bad status codes
                    
                    # The CSV has a header row that starts with "sep=", so we need to skip it
                    csv_content = response.text
                    lines = csv_content.split('\n')
                    # Skip the first line if it starts with "sep="
                    if lines[0].startswith('sep='):
                        csv_content = '\n'.join(lines[1:])
                    
                    # Try to parse with semicolon separator first
                    try:
                        data = pd.read_csv(io.StringIO(csv_content), sep=';')
                    except:
                        # Fall back to comma separator
                        data = pd.read_csv(io.StringIO(csv_content))
                    
                    # Debug info (commented out for cleaner output)
                    # print(f"  CSV columns for station {station_id}: {list(data.columns)}")
                    # print(f"  CSV shape for station {station_id}: {data.shape}")
                    # if not data.empty:
                    #     print(f"  First few rows for station {station_id}:")
                    #     print(data.head())
                    
                    filtered_dataframes = {}
                    # Check if 'Parameter' column exists
                    if 'Parameter' in data.columns and not data.empty:
                        # Ensure DATE_COLL is parsed to datetime and apply date filtering if provided
                        if 'DATE_COLL' in data.columns:
                            try:
                                parsed_dates = pd.to_datetime(data['DATE_COLL'], errors='coerce')
                                data['DATE_COLL'] = parsed_dates
                                if start_date:
                                    data = data[data['DATE_COLL'] >= pd.to_datetime(start_date)]
                                if end_date:
                                    data = data[data['DATE_COLL'] <= pd.to_datetime(end_date)]
                            except Exception:
                                pass
                        for chemical in water_chemicals:
                            if chemical in data['Parameter'].values:
                                chemical_data = data[data['Parameter'] == chemical]
                                # Filter out rows where Result is NaN or empty
                                filtered_data = chemical_data.dropna(subset=['Result'])
                                if not filtered_data.empty:
                                    filtered_dataframes[chemical] = filtered_data
                                    print(f"  Filtered data for {chemical} retrieved successfully for station {station_id}.")
                    else:
                        if not data.empty:
                            print(f"  Warning: 'Parameter' column not found in data for station {station_id}")
                            # Try to use the data as is if it has the expected structure
                            filtered_dataframes['water_quality_data'] = data
                            print(f"  Stored raw data for station {station_id}")
                        else:
                            print(f"  No data available for station {station_id}")
                    
                    if filtered_dataframes:
                        all_station_data[station_id] = filtered_dataframes
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching CSV data for station {station_id}: {e}")
                except pd.errors.EmptyDataError:
                    print(f"Warning: No data found in the CSV file for station {station_id}.")
                except Exception as e:
                    print(f"An unexpected error occurred while processing data for station {station_id}: {e}")
            else:
                print(f"Skipping station {station_id} due to missing dataset name.")

        return all_station_data

    def process(self, raw_data=None, location=None, dataset=None):
        """
        Processes the raw data (DataFrames) into a standardized format of times and values.

        Args:
            raw_data (dict): A dictionary where keys are station IDs and values are dictionaries
                             of chemical parameters and their corresponding DataFrames.
            location (list, optional): Not directly used here as location info is within raw_data. Defaults to None.
            dataset (list, optional): Not directly used here as dataset info is within raw_data. Defaults to None.

        Returns:
            tuple: A tuple containing two dictionaries:
                   - times: A dictionary where keys are (station_id, chemical) tuples and values are lists of timestamps.
                   - values: A dictionary where keys are (station_id, chemical) tuples and values are lists of corresponding values.
        """
        if raw_data is None:
            return {}, {}

        processed_times = {}
        processed_values = {}

        for station_id, chemical_data in raw_data.items():
            for chemical, df in chemical_data.items():
                if not df.empty:
                    # Use the correct column names from the NDGIS data
                    time_col = 'DATE_COLL'
                    value_col = 'Result'

                    if time_col in df.columns and value_col in df.columns:
                        # Convert 'DATE_COLL' to datetime objects
                        try:
                            times = pd.to_datetime(df[time_col]).tolist()
                            key = (str(station_id), chemical)  # Ensure station_id is a string for consistency
                            processed_times[key] = times

                            # Extract the Result values for the chemical
                            values_list = df[value_col].tolist()
                            processed_values[key] = values_list

                        except KeyError:
                            print(f"Warning: '{time_col}' column not found in data for station {station_id}, chemical {chemical}.")
                        except Exception as e:
                            print(f"Error processing time/value columns for station {station_id}, chemical {chemical}: {e}")
                    else:
                        print(f"Warning: Required column ('{time_col}') not found in data for station {station_id}, chemical {chemical}.")

        return processed_times, processed_values

    def store_water_quality_data(self, raw_data, start_date=None, end_date=None):
        """
        Custom storage method for water quality data that stores all parameters
        for the same location and datetime in a single row.
        """
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from sqlclasses import _get_db_connection
        
        if not raw_data:
            return
            
        try:
            conn, cursor = _get_db_connection()
            if not conn or not cursor:
                print("Failed to get database connection.")
                return
                
            # Create a dictionary to group data by location and datetime
            grouped_data = {}
            
            affected_locations = set()
            for station_id, chemical_data in raw_data.items():
                for chemical, df in chemical_data.items():
                    if not df.empty and 'DATE_COLL' in df.columns and 'Result' in df.columns:
                        for _, row in df.iterrows():
                            # Normalize datetime to 'YYYY-MM-DD HH:MM:SS'
                            try:
                                dt_obj = pd.to_datetime(row['DATE_COLL'])
                                datetime_key = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                            except Exception:
                                datetime_key = str(row['DATE_COLL'])
                            location_key = str(station_id)
                            
                            # Create a key for grouping
                            group_key = (location_key, datetime_key)
                            
                            if group_key not in grouped_data:
                                grouped_data[group_key] = {
                                    'location': location_key,
                                    'datetime': datetime_key,
                                    'parameters': {}
                                }
                            
                            # Map chemical name to database column name
                            chemical_mapping = {
                                'Phosphorus (Total) (P)': 'total_phosphorus',
                                'Phosphorus (Total Kjeldahl) (P)': 'total_kjeldahl_phosphorus',
                                'Nitrate + Nitrite (N)': 'nitrate_nitrite',
                                'Nitrate Forms Check': 'nitrate_forms_check',
                                'Nitrate + Nitrite (N) Dis': 'nitrate_nitrite_dissolved',
                                'Nitrogen (Total Kjeldahl)': 'total_kjeldahl_nitrogen',
                                'Nitrogen (TKN-Dissolved)': 'tkn_dissolved',
                                'Nitrogen (Total-Dis)': 'total_nitrogen_dissolved',
                                'E.coli': 'e_coli',
                                'Nitrogen (Total)': 'total_nitrogen',
                                'pH': 'ph',
                                'Ammonia (N)': 'ammonia_nitrogen',
                                'Ammonia (N)-Dissolved': 'ammonia_nitrogen_dissolved',
                                'Ammonia Forms Check': 'ammonia_forms_check',
                                'Diss Ammonia TKN Check': 'diss_ammonia_tkn_check',
                                'Dissolved Phosphorus as P': 'dissolved_phosphorus'
                            }
                            
                            if chemical in chemical_mapping:
                                column_name = chemical_mapping[chemical]
                                # Convert result to float if possible, otherwise store as string
                                try:
                                    result_value = float(row['Result']) if row['Result'] != '*NON-DETECT' else None
                                except (ValueError, TypeError):
                                    result_value = None
                                
                                grouped_data[group_key]['parameters'][column_name] = result_value
                                affected_locations.add(location_key)
            
            # Insert the grouped data into the database
            # Optionally delete existing rows in the date range for affected locations to replace with fresh data
            if start_date:
                start_dt_str = pd.to_datetime(start_date).strftime('%Y-%m-%d %H:%M:%S')
                for loc in affected_locations:
                    if end_date:
                        end_dt_str = pd.to_datetime(end_date).strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute(
                            "DELETE FROM water_quality WHERE location = ? AND datetime >= ? AND datetime <= ?",
                            (loc, start_dt_str, end_dt_str),
                        )
                    else:
                        cursor.execute(
                            "DELETE FROM water_quality WHERE location = ? AND datetime >= ?",
                            (loc, start_dt_str),
                        )
            for group_key, data in grouped_data.items():
                # Build the SQL query dynamically based on available parameters
                columns = ['location', 'datetime'] + list(data['parameters'].keys())
                placeholders = ['?'] * len(columns)
                values = [data['location'], data['datetime']] + list(data['parameters'].values())
                
                sql = f"INSERT OR REPLACE INTO water_quality ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                cursor.execute(sql, values)
            
            conn.commit()
            print(f"Successfully stored {len(grouped_data)} water quality records.")
            
        except Exception as e:
            print(f"Error storing water quality data: {e}")
            if conn:
                conn.rollback()

    def pull(self, location=None, dataset=None, start_date=None, end_date=None):
        """
        Main method to pull and store data from NDGIS for specified locations and datasets.

        Args:
            location (list, optional): A list of station IDs to fetch data for. Defaults to None (fetches all from masterlist).
            dataset (list, optional): A list of water chemical parameters to fetch. Defaults to a predefined list.
            start_date (datetime.date, optional): Not used in this implementation. Defaults to None.
            end_date (datetime.date, optional): Not used in this implementation. Defaults to None.

        Returns:
            tuple: A tuple containing two dictionaries:
                   - times: A dictionary where keys are (station_id, chemical) tuples and values are lists of timestamps.
                   - values: A dictionary where keys are (station_id, chemical) tuples and values are lists of corresponding values.
        """
        raw_data = self.fetch(location, dataset, start_date, end_date)
        if raw_data:
            # Use custom storage method for water quality data
            self.store_water_quality_data(raw_data, start_date=start_date, end_date=end_date)
            
            # Also return the processed data for compatibility
            times, values = self.process(raw_data)
            return times, values
        return {}, {}

    def pull_all(self, start_date, end_date):
        """
        Pull all relevant data for this source for the given date range.
        
        Args:
            start_date (datetime.date): Start date for data retrieval
            end_date (datetime.date): End date for data retrieval
            
        Returns:
            tuple: A tuple containing two dictionaries:
                   - times: A dictionary where keys are (station_id, chemical) tuples and values are lists of timestamps.
                   - values: A dictionary where keys are (station_id, chemical) tuples and values are lists of corresponding values.
        """
        # For NDGIS, we don't use date filtering in the current implementation
        # but we can add it if needed in the future
        return self.pull(location=None, dataset=None, start_date=start_date, end_date=end_date)

if __name__ == '__main__':
    # Example usage:
    ndgis_source = NDGISWaterChem()

    # Pull data for specific station IDs and a subset of chemicals, restricted to 2023-current
    station_list = ['380001']  # Replace with actual station IDs as needed
    chemical_list = ['Phosphorus (Total) (P)', 'Nitrate + Nitrite (N)', 'pH', 'E.coli']
    start_date = date(2023, 1, 1)
    end_date = date.today()
    times, values = ndgis_source.pull(location=station_list, dataset=chemical_list, start_date=start_date, end_date=end_date)

    if times and values:
        print("\nSuccessfully pulled and processed data:")
        for key, time_data in times.items():
            print(f"\nStation: {key[0]}, Chemical: {key[1]}")
            print("Times:", time_data)
            print("Values:", values.get(key))
    else:
        print("\nNo data pulled or an error occurred.")

    # To pull data for all stations in the masterlist and the default chemicals:
    # all_times, all_values = ndgis_source.pull()
    # if all_times and all_values:
    #     print("\nSuccessfully pulled and processed data for all stations (default chemicals):")
    #     # Print some sample data or further process it
    # else:
    #     print("\nNo data pulled for all stations (default chemicals) or an error occurred.")
