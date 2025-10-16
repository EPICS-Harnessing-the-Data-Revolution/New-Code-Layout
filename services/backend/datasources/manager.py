"""
Manager class for coordinating all data sources.
Provides a single point of access for pulling data from multiple sources.
"""

from services.backend.datasources import *
from services.backend.datasources.utils import DateHelper
from services.backend.datasources.config import (
    GAUGES, DAMS, MESONETS, COCORAHS, NOAA, SHADEHILL
)
from typing import Dict, List, Optional, Any


class DataSourceManager:

    def __init__(self):
        """
        Initialize the manager with all data sources.
        Imports are done here to avoid circular imports.
        """

        from services.backend.datasources.noaa_source import NOAADataSource
        from services.backend.datasources.usgs_source import USGSDataSource
        from services.backend.datasources.usace_source import USACEDataSource
        from services.backend.datasources.ndmes_source import NDMESDataSource
        from services.backend.datasources.cocorahs_source import CoCoRaHSDataSource
        from services.backend.datasources.shadehill_source import ShadehillDataSource

        self.sources = {
            "noaa": NOAADataSource(),
            "usgs": USGSDataSource(),
            "usace": USACEDataSource(),
            "ndmes": NDMESDataSource(),
            "cocorahs": CoCoRaHSDataSource(),
            "shadehill": ShadehillDataSource()
        }

        # Map of location sets for each source type
        self.location_sets = {
            "usgs": list(GAUGES),
            "usace": list(DAMS),
            "ndmes": list(MESONETS),
            "cocorahs": list(COCORAHS),
            "noaa": list(NOAA),
            "shadehill": list(SHADEHILL)
        }

    def pull_all_data(self, num_days=30):
        # Get date range
        start_date, end_date = DateHelper.get_date_range(num_days)

        print(f"Pulling data for the last {num_days} days")
        print(f"Start date: {start_date['year']}-{start_date['month']}-{start_date['day']}")
        print(f"End date: {end_date['year']}-{end_date['month']}-{end_date['day']}")
        print("-" * 50)

        # Pull data from each source
        for source_name, source in self.sources.items():
            print(f"\nPulling data from {source_name.upper()} source...")
            try:
                source.pull_all(start_date, end_date)
                print(f"Finished pulling data from {source_name.upper()}")
            except Exception as e:
                print(f"Error pulling data from {source_name}: {e}")

        print("\nAll data pulling complete!")

    def pull_source(self, source_name, num_days=30):
        """
        Pull data from a specific source.
        """

        if source_name not in self.sources:
            print(f"Unknown source: {source_name}")
            print(f"Available sources: {', '.join(self.sources.keys())}")
            return

        # Get date range
        start_date, end_date = DateHelper.get_date_range(num_days)

        print(f"Pulling data from {source_name.upper()} for the last {num_days} days")
        print(f"Start date: {start_date['year']}-{start_date['month']}-{start_date['day']}")
        print(f"End date: {end_date['year']}-{end_date['month']}-{end_date['day']}")
        print("-" * 50)

        try:
            self.sources[source_name].pull_all(start_date, end_date)
            print(f"Finished pulling data from {source_name.upper()}")
        except Exception as e:
            print(f"Error pulling data from {source_name}: {e}")

    def pull_location(self, location, num_days=30):
        start_date, end_date = DateHelper.get_date_range(num_days)

        print(f"Pulling data for {location} for the last {num_days} days")
        print(f"Start date: {start_date['year']}-{start_date['month']}-{start_date['day']}")
        print(f"End date: {end_date['year']}-{end_date['month']}-{end_date['day']}")
        print("-" * 50)

        # Find which sources have this location
        found = False
        for source_name, locations in self.location_sets.items():
            if location in locations:
                found = True
                source = self.sources[source_name]
                print(f"Pulling {location} data from {source_name.upper()} source...")

                try:
                    if source_name == "usgs":
                        for dataset in ["Gauge Height", "Elevation", "Discharge", "Water Temperature"]:
                            self._pull_dataset(source, location, dataset, start_date, end_date)

                    elif source_name == "usace":
                        for dataset in ["Elevation", "Flow Spill", "Flow Powerhouse", "Flow Out",
                                        "Tailwater Elevation", "Energy", "Water Temperature", "Air Temperature"]:
                            self._pull_dataset(source, location, dataset, start_date, end_date)

                    elif source_name == "ndmes":
                        for dataset in ["Average Air Temperature", "Average Relative Humidity",
                                        "Average Bare Soil Temperature", "Average Turf Soil Temperature",
                                        "Maximum Wind Speed", "Average Wind Direction",
                                        "Total Solar Radiation", "Total Rainfall",
                                        "Average Baromatric Pressure", "Average Dew Point",
                                        "Average Wind Chill"]:
                            self._pull_dataset(source, location, dataset, start_date, end_date)

                    elif source_name == "cocorahs":
                        for dataset in ["Precipitation", "Snowfall", "Snow Depth"]:
                            self._pull_dataset(source, location, dataset, start_date, end_date)

                    elif source_name == "noaa":
                        for dataset in ["temperature", "dewpoint", "relativeHumidity", "windChill"]:
                            self._pull_dataset(source, location, dataset, start_date, end_date)

                    elif source_name == "shadehill":
                        # Shadehill only has one location so we pull all datasets
                        source.pull_all(start_date, end_date)

                except Exception as e:
                    print(f"Error pulling {location} data from {source_name}: {e}")

        if not found:
            print(f"No data source found for location: {location}")

    def _pull_dataset(self, source, location, dataset, start_date, end_date):
        """
        Helper to pull a specific dataset and handle exceptions.

        Args:
            source: The data source object
            location: Location to pull data for
            dataset: Dataset to pull
            start_date: Start date
            end_date: End date
        """
        try:
            raw_data = source.fetch(location, dataset, start_date, end_date)
            times, values = source.process(raw_data, location, dataset)
            if times and values:
                source.store(times, values, location, dataset)
                print(f"  Stored {dataset} data for {location}")
        except Exception as e:
            print(f"  Error processing {dataset} for {location}: {e}")

    def get_source(self, source_name):
        return self.sources.get(source_name)

    def list_sources(self):
        return list(self.sources.keys())

    def list_locations(self, source_name=None):
        if source_name:
            if source_name in self.location_sets:
                return {source_name: self.location_sets[source_name]}
            else:
                return {}
        else:
            return self.location_sets