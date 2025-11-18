import argparse
import sys
import os
from datetime import datetime, timedelta
import logging

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.backend.datasources.noaa_source import NOAADataSource
from services.backend.datasources.usgs_source import USGSDataSource
from services.backend.datasources.config import NOAA, GAUGES

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def parse_date(date_string):
    """
    Parse date string in format YYYY-MM-DD to datetime object.
    
    Args:
        date_string: Date string in YYYY-MM-DD format
        
    Returns:
        datetime object
        
    Raises:
        ValueError: If date format is invalid
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_string}. Use YYYY-MM-DD format.")

def get_date_dict(dt):
    """
    Convert datetime object to dictionary format expected by data sources.
    
    Args:
        dt: datetime object
        
    Returns:
        Dictionary with 'year', 'month', 'day' keys
    """
    return {
        'year': dt.year,
        'month': dt.month,
        'day': dt.day
    }

def fetch_noaa_data(start_date, end_date, location=None, dataset=None):
    """
    Fetch data from NOAA source.
    
    Args:
        start_date: Start date as datetime object
        end_date: End date as datetime object
        location: Specific location to fetch (optional)
        dataset: Specific dataset to fetch (optional)
    """
    logger.info("Initializing NOAA data source...")
    noaa_source = NOAADataSource()
    
    # Convert dates to dictionary format
    start_dict = get_date_dict(start_date)
    end_dict = get_date_dict(end_date)
    
    if location and dataset:
        # Fetch specific location and dataset
        logger.info(f"Fetching NOAA data for {location} - {dataset}")
        
        # Map location name if needed
        mapped_location = noaa_source.location_name_mapping.get(location)
        if not mapped_location:
            logger.error(f"Location '{location}' not found in NOAA location mapping")
            return False
            
        if mapped_location not in noaa_source.location_dict:
            logger.error(f"Location '{mapped_location}' not found in NOAA location dictionary")
            return False
            
        if dataset not in noaa_source.dataset_map:
            logger.error(f"Dataset '{dataset}' not found in NOAA dataset mapping")
            logger.info(f"Available datasets: {list(noaa_source.dataset_map.keys())}")
            return False
        
        try:
            raw_data = noaa_source.fetch(mapped_location, dataset, start_date, end_date)
            if raw_data:
                times, values = noaa_source.process(raw_data, mapped_location, dataset)
                if times and values:
                    noaa_source.store(times, values, location, dataset)
                    logger.info(f"Successfully stored {len(times)} records for {location} - {dataset}")
                    return True
                else:
                    logger.warning(f"No data processed for {location} - {dataset}")
                    return False
            else:
                logger.warning(f"No raw data fetched for {location} - {dataset}")
                return False
        except Exception as e:
            logger.error(f"Error fetching NOAA data for {location} - {dataset}: {e}")
            return False
    else:
        # Fetch all data
        logger.info("Fetching all NOAA data...")
        return noaa_source.pull_all(start_dict, end_dict)

def fetch_usgs_data(start_date, end_date, location=None, dataset=None):
    """
    Fetch data from USGS source.
    
    Args:
        start_date: Start date as datetime object
        end_date: End date as datetime object
        location: Specific location to fetch (optional)
        dataset: Specific dataset to fetch (optional)
    """
    logger.info("Initializing USGS data source...")
    usgs_source = USGSDataSource()
    
    # Convert dates to dictionary format
    start_dict = get_date_dict(start_date)
    end_dict = get_date_dict(end_date)
    
    if location and dataset:
        # Fetch specific location and dataset
        logger.info(f"Fetching USGS data for {location} - {dataset}")
        
        if location not in usgs_source.location_dict:
            logger.error(f"Location '{location}' not found in USGS location dictionary")
            logger.info(f"Available locations: {list(usgs_source.location_dict.keys())}")
            return False
        
        # Check if dataset is available for this location
        available_datasets = ["Gauge Height", "Elevation", "Discharge", "Water Temperature"]
        if dataset not in available_datasets:
            logger.error(f"Dataset '{dataset}' not found in USGS dataset mapping")
            logger.info(f"Available datasets: {available_datasets}")
            return False
        
        try:
            raw_data = usgs_source.fetch(location, dataset, start_dict, end_dict)
            if raw_data:
                times, values = usgs_source.process(raw_data, location, dataset)
                if times and values:
                    usgs_source.store(times, values, location, dataset)
                    logger.info(f"Successfully stored {len(times)} records for {location} - {dataset}")
                    return True
                else:
                    logger.warning(f"No data processed for {location} - {dataset}")
                    return False
            else:
                logger.warning(f"No raw data fetched for {location} - {dataset}")
                return False
        except Exception as e:
            logger.error(f"Error fetching USGS data for {location} - {dataset}: {e}")
            return False
    else:
        # Fetch all data
        logger.info("Fetching all USGS data...")
        return usgs_source.pull_all(start_dict, end_dict)

def main():
    """
    Main function to handle command line arguments and execute data fetching.
    """
    parser = argparse.ArgumentParser(
        description="Fetch data from NOAA or USGS data sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all NOAA data for the last 30 days
  python fetch_data.py --source noaa --days 30
  
  # Fetch all USGS data for specific date range
  python fetch_data.py --source usgs --start-date 2024-01-01 --end-date 2024-01-31
  
  # Fetch specific NOAA location and dataset
  python fetch_data.py --source noaa --location Bismarck --dataset "Average Temperature" --days 7
  
  # Fetch specific USGS location and dataset
  python fetch_data.py --source usgs --location Bismarck --dataset "Gauge Height" --days 7
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--source',
        choices=['noaa', 'usgs'],
        required=True,
        help='Data source to use (noaa or usgs)'
    )
    
    # Date arguments (mutually exclusive group)
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        '--start-date',
        type=str,
        help='Start date in YYYY-MM-DD format'
    )
    date_group.add_argument(
        '--days',
        type=int,
        help='Number of days back from today to fetch data'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date in YYYY-MM-DD format (defaults to today if not specified)'
    )
    
    # Optional arguments for specific data fetching
    parser.add_argument(
        '--location',
        type=str,
        help='Specific location to fetch data for (optional)'
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        help='Specific dataset to fetch (optional)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine date range
    if args.days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
    else:
        start_date = parse_date(args.start_date)
        if args.end_date:
            end_date = parse_date(args.end_date)
        else:
            end_date = datetime.now()
    
    # Validate date range
    if start_date > end_date:
        logger.error("Start date cannot be after end date")
        sys.exit(1)
    
    logger.info(f"Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Fetch data based on source
    success = False
    if args.source == 'noaa':
        success = fetch_noaa_data(start_date, end_date, args.location, args.dataset)
    elif args.source == 'usgs':
        success = fetch_usgs_data(start_date, end_date, args.location, args.dataset)
    
    if success:
        logger.info("Data fetching completed successfully!")
        sys.exit(0)
    else:
        logger.error("Data fetching failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()