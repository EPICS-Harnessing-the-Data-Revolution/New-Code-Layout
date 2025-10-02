import os
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import requests


class DataSource(ABC):
    def __init__(self, name, data_type):
        self.name = name
        self.data_type = data_type

    @abstractmethod
    def fetch(self, location=None, dataset=None, start_date=None, end_date=None):
        pass

    @abstractmethod
    def process(self, raw_data=None, location=None, dataset=None):
        """
        Process the raw data into a standardized format.
        Must be implemented by derived classes.
        """
        pass

    def store(self, times=None, values=None, location=None, dataset=None):
        """
        Store the processed data in the sql database.
        """
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from sqlclasses import updateDictionary

        updateDictionary(times, values, location, dataset, self.data_type)

    def pull(self, location=None, dataset=None, start_date=None, end_date=None):
        """
        Main method to pull and store data from this source.
        """

        raw_data = self.fetch(location, dataset, start_date, end_date)
        times, values = self.process(raw_data, location, dataset)
        # Ensure times and values are not empty before storing
        if times and values:
            self.store(times, values, location, dataset)
        else:
            # Optionally log that no data was processed or stored
            # print(f"No data processed for {location} - {dataset}")
            pass
        return times, values

    @abstractmethod
    def pull_all(self, start_date, end_date):
        """
        Pull all relevant data for this source for the given date range.
        Must be implemented by derived classes.
        """
        pass
