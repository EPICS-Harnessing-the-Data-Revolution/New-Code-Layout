import csv
import io
import os

import pandas as pd
import requests

from services.backend.datasources.base import DataSource
from services.backend.datasources.config import NDMES_STATIONS
from services.backend.datasources.utils import DataParser, DateHelper


class NDMESDataSource(DataSource):
    """
    Data source for North Dakota Mesonet data.
    """

    def __init__(self):
        super().__init__("NDMES", "mesonet")
        self.location_dict = NDMES_STATIONS

    def fetch(self, location, dataset=None, start_date=None, end_date=None):
        """
        Fetch mesonet data from NDSU NDAWN.
        """
        location_data = self.location_dict[location]
        station = location_data[0]

        # Takes the date in a string format
        if isinstance(start_date, dict):
            s_year = start_date.get("year", "")
            s_month = start_date.get("month", "")
            s_day = start_date.get("day", "")
        elif isinstance(start_date, str):
            s_year, s_month, s_day = start_date[0:4], start_date[4:6], start_date[6:8]
        else:
            print(f"Invalid start_date format: {start_date}")
            return None

        if isinstance(end_date, dict):
            e_year = end_date.get("year", "")
            e_month = end_date.get("month", "")
            e_day = end_date.get("day", "")
        elif isinstance(end_date, str):
            e_year, e_month, e_day = end_date[0:4], end_date[4:6], end_date[6:8]
        else:
            print(f"Invalid end_date format: {end_date}")
            return None

        url_csv = f"https://ndawn.ndsu.nodak.edu/table.csv?ttype=hourly&station={station}&begin_date={s_year}-{s_month}-{s_day}&end_date={e_year}-{e_month}-{e_day}"
        try:
            response = requests.get(url_csv)

            if response.status_code != 200:
                print(
                    f"Error fetching NDMES data for {location}: HTTP {response.status_code}"
                )
                return None

            data = pd.read_csv(io.StringIO(response.text), skiprows=3)
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error fetching NDMES data for {location}: {e}")
            return None

    def process(self, raw_data, location, dataset):
        """
        Process the raw NDMES data.
        """
        if raw_data is None:
            print(f"No data to process for {location}")
            return [], []

        try:
            list_to_del = [
                "Avg Air Temp Flag",
                "Avg Rel Hum Flag",
                "Avg Bare Soil Temp Flag",
                "Avg Turf Soil Temp Flag",
                "Avg Wind Speed Flag",
                "Max Wind Speed Flag",
                "Avg Wind Dir Flag",
                "Avg Wind Dir SD Flag",
                "Avg Dew Point Flag",
                "Avg Baro Press Flag",
                "Avg Sol Rad Flag",
                "Total Rainfall Flag",
            ]

            list_to_del_2 = ["Station Name", "Latitude", "Longitude", "Elevation"]

            df = raw_data

            df2 = df.iloc[1:]

            for i in list_to_del:
                if i in df2.columns:
                    del df2[i]

            for i in list_to_del_2:
                if i in df2.columns:
                    del df2[i]

            years = df2["Year"].tolist()
            months = df2["Month"].tolist()
            days = df2["Day"].tolist()
            hours = df2["Hour"].tolist()

            times = []
            for i in range(0, len(years)):
                month = int(months[i])
                month_str = f"0{month}" if month < 10 else str(month)

                day = int(days[i])
                day_str = f"0{day}" if day < 10 else str(day)

                hour_int = int(hours[i])
                if hour_int < 1000:
                    hour_str = f"0{hour_int // 100}:{hour_int % 100}"
                else:
                    hour_str = f"{hour_int // 100}:{hour_int % 100}"

                times.append(f"{int(years[i])}-{month_str}-{day_str} {hour_str}")

            datasets = {
                "Average Air Temperature": df2["Avg Air Temp"].tolist(),
                "Average Relative Humidity": df2["Avg Rel Hum"].tolist(),
                "Average Bare Soil Temperature": df2["Avg Bare Soil Temp"].tolist(),
                "Average Turf Soil Temperature": df2["Avg Turf Soil Temp"].tolist(),
                "Maximum Wind Speed": df2["Avg Wind Speed"].tolist(),
                "Average Wind Direction": df2["Avg Wind Dir"].tolist(),
                "Total Solar Radiation": df2["Avg Sol Rad"].tolist(),
                "Total Rainfall": df2["Total Rainfall"].tolist(),
                "Average Baromatric Pressure": df2["Avg Baro Press"].tolist(),
                "Average Dew Point": df2["Avg Dew Point"].tolist(),
                "Average Wind Chill": df2["Avg Wind Chill"].tolist(),
            }

            if dataset in datasets:
                values = DataParser.parse_numeric_list(datasets[dataset])
                return times, values
            else:
                return [], []

        except Exception as e:
            print(f"Error processing NDMES data for {location}: {e}")
            return [], []

    def pull_all(self, start_date, end_date):
        """
        Pull data for all locations and datasets.

        Args:
            start_date: Start date dictionary with year, month, day
            end_date: End date dictionary with year, month, day
        """
        datasets = [
            "Average Air Temperature",
            "Average Relative Humidity",
            "Average Bare Soil Temperature",
            "Average Turf Soil Temperature",
            "Maximum Wind Speed",
            "Average Wind Direction",
            "Total Solar Radiation",
            "Total Rainfall",
            "Average Baromatric Pressure",
            "Average Dew Point",
            "Average Wind Chill",
        ]

        # Convert date dictionaries to strings for the API if needed
        if isinstance(start_date, dict):
            start_date_str = (
                f"{start_date['year']}{start_date['month']}{start_date['day']}"
            )
        else:
            start_date_str = start_date

        if isinstance(end_date, dict):
            end_date_str = f"{end_date['year']}{end_date['month']}{end_date['day']}"
        else:
            end_date_str = end_date

        for location in self.location_dict.keys():
            print(f"Pulling NDMES data for {location}...")

            try:
                # Fetch the data once
                raw_data = self.fetch(location, None, start_date, end_date)

                if raw_data is not None:
                    # Process and store each dataset
                    for dataset in datasets:
                        times, values = self.process(raw_data, location, dataset)
                        if times and values:
                            self.store(times, values, location, dataset)
                        else:
                            print(f"No data for {location} - {dataset}")
                else:
                    print(f"Failed to fetch data for {location}")
            except Exception as e:
                print(f"Error processing NDMES data for {location}: {e}")
if __name__ == "__main__":
    ndmes = NDMESDataSource()
    # Example: print date helper output
    print(DateHelper.string_to_list("20240601"))
    # Fetch and print raw data for Fort Yates, Average Air Temperature, for a short date range
    start = DateHelper.string_to_list("20240601")
    end = DateHelper.string_to_list("20240607")
    raw_data = ndmes.fetch("Fort Yates", dataset="Average Air Temperature", start_date=start, end_date=end)
    print(raw_data)
    # Process and print times/values for the same
    if raw_data is not None:
        times, values = ndmes.process(raw_data, "Fort Yates", "Average Air Temperature")
        print(times)
        print(values)
        # Output to CSV file
        import csv
        with open("ndmes_test_output.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Time", "Average Air Temperature"])
            for t, v in zip(times, values): 
                writer.writerow([t, v])
        print("Results written to ndmes_test_output.csv")
