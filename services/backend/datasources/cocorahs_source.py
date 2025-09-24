from json import loads

import requests

from .base import DataSource
from .config import COCORAHS_STATIONS

class CoCoRaHSDataSource(DataSource):
    """
    Data source for CoCoRaHS precipitation and snow data.
    """

    def __init__(self):
        super().__init__("CoCoRaHS", "cocorahs")
        self.station_dict = COCORAHS_STATIONS

    def fetch(self, location=None, dataset=None, start_date=None, end_date=None):
        if location not in self.station_dict:
            print(f"Unknown CoCoRaHS location: {location}")
            return None

        station_info = self.station_dict[location]
        station_id = station_info[0]
        start_date_str = station_info[1]  # Use earliest date from dictionary

        # Format end date if provided, otherwise use station's first date
        end_date_str = end_date if isinstance(end_date, str) else start_date_str

        # Create ACIS API URL
        url = self.get_link(station_id, start_date_str, end_date_str)

        try:
            # Make request
            response = requests.get(url)

            if response.status_code != 200:
                print(
                    f"Error fetching CoCoRaHS data for {location}: HTTP {response.status_code}"
                )
                return None

            # Parse JSON response
            results_dict = loads(response.text)
            return results_dict

        except requests.exceptions.RequestException as e:
            print(f"Error fetching CoCoRaHS data for {location}: {e}")
            return None

        except Exception as e:
            print(f"Error parsing CoCoRaHS data for {location}: {e}")
            return None

    def process(self, raw_data, location, dataset):
        if not raw_data or "data" not in raw_data:
            return [], []

        # Get the dict location (for database storage)
        dict_location = (
            self.station_dict[location][2]
            if location in self.station_dict
            else location
        )

        times = []
        values = []

        # Extract all data values
        data_list = raw_data["data"]

        # Process each data entry
        for i in range(len(data_list)):
            # Convert time string
            date_str = data_list[i][0]
            time_str = self.change_time_string_ACIS(date_str)
            times.append(time_str)

            # Get the appropriate value based on the dataset
            if dataset == "Precipitation":
                try:
                    values.append(float(data_list[i][1]))
                except:
                    values.append(None)
            elif dataset == "Snowfall":
                try:
                    values.append(float(data_list[i][2]))
                except:
                    values.append(None)
            elif dataset == "Snow Depth":
                try:
                    values.append(float(data_list[i][3]))
                except:
                    values.append(None)
            else:
                values.append(None)

        return times, values

    def pull_all(self, start_date, end_date):
        """
        Pull data for all locations and datasets.

        Args:
            start_date: Not used for CoCoRaHS
            end_date: End date string in format YYYYMMDD
        """
        datasets = ["Precipitation", "Snowfall", "Snow Depth"]

        if isinstance(end_date, dict):
            end_date_str = f"{end_date['year']}{end_date['month']}{end_date['day']}"
        else:
            # Use current date if not provided
            from datetime import datetime

            now = datetime.now()
            end_date_str = now.strftime("%Y%m%d")

        for location in self.station_dict.keys():
            print(f"Pulling CoCoRaHS data for {location}...")

            try:
                raw_data = self.fetch(location, None, None, end_date_str)

                if raw_data:
                    for dataset in datasets:
                        times, values = self.process(raw_data, location, dataset)
                        if times and values:
                            dict_location = self.station_dict[location][2]
                            self.store(times, values, dict_location, dataset)
            except Exception as e:
                print(f"Error processing CoCoRaHS data for {location}: {e}")

    # HELPER FUNCTIONS
    def get_link(self, station_id, start_date, end_date):
        """
        Create API URL for data retrieval.
        """

        params = f'{{"sid":"{station_id}","sdate":"{start_date}","edate":"{end_date}","elems":"pcpn,snow,snwd"}}'
        url = f"http://data.rcc-acis.org/StnData?params={params}"
        return url

    def change_time_string_ACIS(self, date_str):
        """
        Convert to database format.

        Input: date_str: Date string in format YYYY-MM-DD

        Returns:
            Formatted datetime string (YYYY-MM-DD HH:MM:SS)
        """
        year, month, day = date_str.split("-")
        return f"{year}-{month}-{day} 00:00:00"
