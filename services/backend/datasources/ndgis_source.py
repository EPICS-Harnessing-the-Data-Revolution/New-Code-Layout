# ndgis_source.py
from datetime import datetime, date
import os
import requests
import pandas as pd
import io
import sqlite3

from services.backend.datasources.base2 import DataSource
from services.backend.sqlclasses import _get_db_connection


class NDGISWaterChem(DataSource):
    """
    Data source for NDGIS water chemistry data using base2 template.
    """
    
    def __init__(self, start_date=None, format=None):
        super().__init__("NDGIS", start_date, format)
        self.masterlist_path = r'INSERT THE PATH TO THE MASTERLIST HERE'  # Path to your Excel masterlist
        self.data = []  # Store raw data from _pull
        self.processed = []  # Store processed data from _process
        
        # Default water chemicals to fetch
        self.water_chemicals = [
            'Phosphorus (Total) (P)', 'Phosphorus (Total Kjeldahl) (P)', 'Nitrate + Nitrite (N)',
            'Nitrate Forms Check', 'Nitrate + Nitrite (N) Dis', 'Nitrogen (Total Kjeldahl)',
            'Nitrogen (TKN-Dissolved)', 'Nitrogen (Total-Dis)', 'E.coli', 'Nitrogen (Total)', 
            'pH', 'Ammonia (N)', 'Ammonia (N)-Dissolved', 'Ammonia Forms Check', 
            'Diss Ammonia TKN Check', 'Dissolved Phosphorus as P'
        ]
        
        # Chemical name to database column mapping
        self.chemical_mapping = {
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
                    "outFields": "SITE_ID",
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
                    sid = attrs.get("SITE_ID")  # API returns SITE_ID in uppercase
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

    def _pull(self):
        """
        Pull raw NDGIS water chemistry data for all stations.
        Stores raw data in self.data as a list of dictionaries with station_id and chemical DataFrames.
        """
        self.data = []
        
        # Get station IDs
        station_ids = []
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
                return

        # Fetch data for each station
        for station_id in station_ids:
            print(f"Fetching data for station ID: {station_id}")
            waterchem_url = f"https://deq.nd.gov/Webservices_SWDataApp/DownloadStationsData/GetStationsWaterChemData/{station_id}"
            waterchem_dataset_name = self._get_dataset_name(waterchem_url)

            if waterchem_dataset_name:
                waterchem_data_url = f"https://deq.nd.gov/WQ/3_Watershed_Mgmt/SWDataApp/downloaddata/{waterchem_dataset_name}.csv"
                try:
                    response = requests.get(waterchem_data_url)
                    response.raise_for_status()
                    
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
                    
                    # Apply date filtering if cutoff is set
                    if 'DATE_COLL' in data.columns and isinstance(self.cutoff, datetime):
                        try:
                            parsed_dates = pd.to_datetime(data['DATE_COLL'], errors='coerce')
                            data['DATE_COLL'] = parsed_dates
                            data = data[data['DATE_COLL'] > self.cutoff]
                        except Exception:
                            pass
                    
                    # Filter by chemicals
                    filtered_dataframes = {}
                    if 'Parameter' in data.columns and not data.empty:
                        for chemical in self.water_chemicals:
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
                        else:
                            print(f"  No data available for station {station_id}")
                    
                    if filtered_dataframes:
                        self.data.append({
                            'station_id': station_id,
                            'chemical_data': filtered_dataframes
                        })
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching CSV data for station {station_id}: {e}")
                except pd.errors.EmptyDataError:
                    print(f"Warning: No data found in the CSV file for station {station_id}.")
                except Exception as e:
                    print(f"An unexpected error occurred while processing data for station {station_id}: {e}")
            else:
                print(f"Skipping station {station_id} due to missing dataset name.")

    def _process(self):
        """
        Process raw NDGIS data in self.data into grouped format for storage.
        Groups all parameters for the same location and datetime into single records.
        Stores grouped data in self.processed.
        """
        self.processed = []
        
        for entry in self.data:
            station_id = entry.get('station_id')
            chemical_data = entry.get('chemical_data', {})
            
            # Group data by location and datetime
            grouped_data = {}
            
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
                        group_key = (location_key, datetime_key)
                        
                        if group_key not in grouped_data:
                            grouped_data[group_key] = {
                                'location': location_key,
                                'datetime': datetime_key,
                                'parameters': {}
                            }
                        
                        # Map chemical to database column and store value
                        if chemical in self.chemical_mapping:
                            column_name = self.chemical_mapping[chemical]
                            try:
                                result_value = float(row['Result']) if row['Result'] != '*NON-DETECT' else None
                            except (ValueError, TypeError):
                                result_value = None
                            
                            grouped_data[group_key]['parameters'][column_name] = result_value
            
            # Add all grouped records to processed
            for group_key, data in grouped_data.items():
                self.processed.append(data)

    def _push(self):
        """
        Push processed NDGIS data into SQL database using water_quality table.
        Uses custom storage that groups all parameters for same location/datetime in one row.
        """
        if not self.processed:
            return
        
        try:
            conn, cursor = _get_db_connection()
            if not conn or not cursor:
                print("Failed to get database connection.")
                return
            
            for data in self.processed:
                # Build the SQL query dynamically based on available parameters
                columns = ['location', 'datetime'] + list(data['parameters'].keys())
                placeholders = ['?'] * len(columns)
                values = [data['location'], data['datetime']] + list(data['parameters'].values())
                
                sql = f"INSERT OR REPLACE INTO water_quality ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                cursor.execute(sql, values)
            
            conn.commit()
            print(f"Successfully stored {len(self.processed)} water quality records.")
            
        except sqlite3.Error as e:
            print(f"Database error during update: {e}")
            if conn:
                conn.rollback()
        except Exception as e:
            print(f"Error storing water quality data: {e}")
            if conn:
                conn.rollback()

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
