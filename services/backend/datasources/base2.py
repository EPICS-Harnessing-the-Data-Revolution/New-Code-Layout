#Author: Kartik Jairam
#Date: 10/23/2025
#Purpose: To serve as a base class for all sources to inherit from

from abc import ABC, abstractmethod
from datetime import datetime

class DataSource(ABC):
    """
    Abstract base class for all data sources.
    Provides a standard interface for fetching, processing, and storing data.
    """

    def __init__(self, source, start_date=None, format = None):
        self.source = source
        if start_date is not None and format is not None:
            self.cutoff = datetime.strptime(start_date, format)
        else:
            self.cutoff = None


    @abstractmethod
    def _pull(self):
        """
        Pulls raw data from the data source and stores data as a member of the class.
        Must be implemented by subclasses.
        Protected method.
        This method should have different processes to pull specific data based on the arguments above
        """
        pass

    @abstractmethod
    def _process(self):
        """
        Process the raw data into a standardized format.
        Uses member data.
        Must be implemented by subclasses.
        Protected method.
        """
        pass

    @abstractmethod
    def _push(self):
        """
        Push the processed data in the SQL database.
        Uses member data.
        Must be implmented by subclass
        Protected method.        
        """
        pass

    def update(self, start_date=None):
        """
        Fetches the data, processes, and then appends the data to the database
        Public method.
        updates.py should use this
        """
        self._pull()
        self._process()
        self._push()

