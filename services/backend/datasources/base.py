import os
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

class DataSource(ABC):
    """
    Abstract base class for all data sources.
    Provides a standard interface for fetching, processing, and storing data.
    """

    def __init__(self, name: str, data_type: str):
        self.name = name
        self.data_type = data_type

    @abstractmethod
    def fetch(self, location=None, dataset=None, start_date=None, end_date=None):
        """
        Fetch raw data from the data source.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def process(self, raw_data=None, location=None, dataset=None):
        """
        Process the raw data into a standardized format (e.g., times and values).
        Must be implemented by subclasses.
        """
        pass

    def store(self, times=None, values=None, location=None, dataset=None):
        """
        Store the processed data in the SQL database.
        """
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from sqlclasses import updateDictionary

        updateDictionary(times, values, location, dataset, self.data_type)

    def pull(self, location=None, dataset=None, start_date=None, end_date=None):
        """
        Main method to fetch, process, and store data from this source.
        Returns processed times and values.
        """
        raw_data = self.fetch(location, dataset, start_date, end_date)
        times, values = self.process(raw_data, location, dataset)
        if times and values:
            self.store(times, values, location, dataset)
        return times, values

    @abstractmethod
    def pull_all(self, start_date, end_date):
        """
        Pull all relevant data for this source for the given date range.
        Must be implemented by subclasses.
        """
        pass