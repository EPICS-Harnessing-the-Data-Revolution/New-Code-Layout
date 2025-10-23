#Author: Kartik Jairam
#Date: 10/23/2025
#Purpose: To serve as a base class for all sources to inherit from

from abc import ABC, abstractmethod

class DataSource(ABC):
    """
    Abstract base class for all data sources.
    Provides a standard interface for fetching, processing, and storing data.
    """

    def __init__(self):
        pass

    @abstractmethod
    def _pull(self, location=None, dataset=None, start_date=None, end_date=None):
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

    def pull(self, location=None, dataset=None, start_date=None, end_date=None):
        """
        Fetches the data, processes, and then appends the data to the database
        Public method.
        updates.py should use this
        """
        self._pull(location=None, dataset=None, start_date=None, end_date=None)
        self._process()
        self._push()

