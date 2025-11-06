import logging
import os
from datetime import datetime

import requests

from services.backend.datasources.config import NOAA
from services.backend.datasources.base import DataSource

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class NOAADataSource(DataSource):
    def __init__(self):
        super().__init__(
            "NOAA", "noaa_weather"
        )  # Changed data_type slightly for clarity
        # Using GHCND station IDs found via NOAA's tool
        self.location_dict = {
            "Bismarck, ND": "GHCND:USW00024011",
            "Grand Forks, ND": "GHCND:USW00014916",
            "Minot, ND": "GHCND:USW00024013",
            "Williston, ND": "GHCND:USW00024014",
        }
        # Mapping of user-friendly dataset names to NOAA datatype IDs
        self.dataset_map = {
            "Average Temperature": "TAVG",
            "Max Temperature": "TMAX",
            "Min Temperature": "TMIN",
            "Precipitation": "PRCP",
            # Add more mappings as needed (e.g., AWND for wind speed)
        }
        # Map from constants.NOAA location names to self.location_dict keys
        self.location_name_mapping = {
            "Bismarck": "Bismarck, ND",
            "Minot": "Minot, ND",
            "Williston/Basin": "Williston, ND",
            # Add more mappings as needed
        }
        self.api_base_url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
        # IMPORTANT: NOAA API requires a token. This should be securely managed.
        # Using an environment variable 'NOAA_API_TOKEN' is recommended.
        self.api_token = os.getenv(
            "NOAA_API_TOKEN", "WkaDdDnFDuEUpiUEFiNMFcLcNKVsQgtp"
        )  # Replace YOUR_DEFAULT_TOKEN or set env var
        if self.api_token == "YOUR_DEFAULT_TOKEN":
            logger.warning(
                "NOAA_API_TOKEN environment variable not set. Using default placeholder."
            )

    def fetch(self, location=None, dataset=None, start_date=None, end_date=None):
        """
        Fetches data from the NOAA CDO API V2.
        """
        if not location or location not in self.location_dict:
            logger.error(f"Invalid or missing location: {location}")
            return None
        if not dataset or dataset not in self.dataset_map:
            logger.error(f"Invalid or missing dataset: {dataset}")
            return None
        if not start_date or not end_date:
            logger.error("Start date and end date are required.")
            return None

        station_id = self.location_dict[location]
        datatype_id = self.dataset_map[dataset]
        # Format dates as YYYY-MM-DD strings
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        headers = {"token": self.api_token}
        params = {
            "datasetid": "GHCND",  # Global Historical Climatology Network Daily
            "stationid": station_id,
            "datatypeid": datatype_id,  
            "startdate": start_date_str,
            "enddate": end_date_str,
            "units": "standard",  # Use standard units (e.g., Fahrenheit for temp)
            "limit": 1000,  # Max limit per request
            "offset": 0,
            "includemetadata": "false",  # Don't need metadata for processing
        }

        all_results = []
        logger.info(
            f"Fetching NOAA data for {location} ({datatype_id}) from {start_date_str} to {end_date_str}"
        )
        
        while True:
            try:
                response = requests.get(
                    self.api_base_url, headers=headers, params=params
                )
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                data = response.json()

                results = data.get("results", [])
                if not results:
                    logger.info(
                        f"No results found for {location} ({datatype_id}) in this batch (offset {params['offset']})."
                    )
                    break  # Exit loop if no results in the current response

                all_results.extend(results)

                # Check pagination metadata
                metadata = data.get("metadata", {}).get("resultset", {})
                count = metadata.get("count", 0)
                offset = metadata.get("offset", 0)
                limit = metadata.get("limit", 0)

                logger.debug(
                    f"Fetched batch: offset={offset}, limit={limit}, count={count}, results_in_batch={len(results)}"
                )

                if (offset + limit) >= count:
                    logger.info(f"Finished fetching all {count} records.")
                    break  # Exit loop if all results fetched

                # Prepare for the next request
                params["offset"] += limit
                logger.debug(f"Requesting next batch with offset {params['offset']}")

            except requests.exceptions.HTTPError as e:
                # Specifically log HTTP errors like 4xx/5xx
                logger.error(
                    f"HTTP Error fetching NOAA data for {location} ({datatype_id}): {e.response.status_code} - {e.response.text}"
                )
                return None  # Stop fetching on error
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Network error fetching NOAA data for {location} ({datatype_id}): {e}"
                )
                return None  # Stop fetching on error
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during fetch for {location} ({datatype_id}): {e}"
                )
                return None  # Stop fetching on unexpected error

        logger.info(
            f"Successfully fetched {len(all_results)} records for {location} - {dataset}"
        )
        return all_results

    def process(self, raw_data=None, location=None, dataset=None):
        """
        Processes raw data fetched from NOAA API.
        """
        if raw_data is None:
            logger.warning(
                f"No raw data provided for processing: {location} - {dataset}"
            )
            return [], []
        if not isinstance(raw_data, list):
            logger.error(
                f"Invalid raw_data format for processing: Expected list, got {type(raw_data)}"
            )
            return [], []

        times = []
        values = []

        # NOAA GHCND temperature values are often in tenths of degrees C/F.
        # Precipitation is often in tenths of mm/inches.
        # Assuming 'standard' units: Temp in F, Precip in inches.
        # We divide by 10.0 for these specific datasets.
        needs_scaling = dataset in [
            "Average Temperature",
            "Max Temperature",
            "Min Temperature",
            "Precipitation",
        ]
        scaling_factor = 10.0 if needs_scaling else 1.0

        logger.info(
            f"Processing {len(raw_data)} raw records for {location} - {dataset}"
        )
        for record in raw_data:
            try:
                # Ensure record is a dictionary
                if not isinstance(record, dict):
                    logger.warning(f"Skipping non-dictionary record: {record}")
                    continue

                # Date format from API is typically 'YYYY-MM-DDTHH:MM:SS'
                timestamp_str = record.get("date")
                value_str = record.get("value")  # Value comes as a number in JSON

                if timestamp_str and value_str is not None:
                    # Parse the timestamp
                    timestamp = datetime.fromisoformat(timestamp_str)
                    times.append(timestamp)

                    # Convert value to float and scale if necessary
                    processed_value = float(value_str) / scaling_factor
                    values.append(processed_value)
                else:
                    logger.warning(
                        f"Skipping record with missing date or value: {record}"
                    )

            except ValueError as e:
                logger.error(f"Error processing record value {record}: {e}")
            except TypeError as e:
                logger.error(f"Type error processing record {record}: {e}")
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during processing record {record}: {e}"
                )

        logger.info(
            f"Successfully processed {len(times)} data points for {location} - {dataset}"
        )
        return times, values

    def pull_all(self, start_date=None, end_date=None, num_days: int = None):
        """
        Pull all NOAA data for all supported locations and datasets.

        Args:
            start_date: Dictionary with 'year', 'month', 'day' keys or a datetime.datetime
            end_date: Dictionary with 'year', 'month', 'day' keys or a datetime.datetime
            num_days: If provided and start_date/end_date are None, pull the last num_days up to today.
        """
        # If caller requested a relative window, compute datetimes
        if (not start_date or not end_date) and num_days:
            from datetime import datetime, timedelta

            end_datetime = datetime.utcnow()
            start_datetime = end_datetime - timedelta(days=int(num_days))
        else:
            # Convert dict inputs to datetimes if necessary
            try:
                if isinstance(start_date, dict):
                    start_datetime = datetime(
                        int(start_date["year"]), int(start_date["month"]), int(start_date["day"])
                    )
                elif isinstance(start_date, datetime):
                    start_datetime = start_date
                else:
                    start_datetime = None

                if isinstance(end_date, dict):
                    end_datetime = datetime(
                        int(end_date["year"]), int(end_date["month"]), int(end_date["day"])
                    )
                elif isinstance(end_date, datetime):
                    end_datetime = end_date
                else:
                    end_datetime = None
            except Exception as e:
                logger.error(f"Invalid date input to pull_all: {e}")
                return False

        if not start_datetime or not end_datetime:
            logger.error("Start date and end date are required.")
            return False

        # Ensure dates are in the correct order
        if start_datetime > end_datetime:
            logger.error(
                f"Start date {start_datetime} is after end date {end_datetime}"
            )
            return False

        success_count = 0
        error_count = 0

        # Loop through all locations in the NOAA list (from constants)
        for loc_name in NOAA:
            # Try to map the location name to a key in self.location_dict
            mapped_location = self.location_name_mapping.get(loc_name)

            if not mapped_location:
                logger.warning(
                    f"No mapping found for NOAA location: {loc_name}. Skipping."
                )
                continue

            if mapped_location not in self.location_dict:
                logger.warning(
                    f"Location '{mapped_location}' not in self.location_dict. Skipping."
                )
                continue

            logger.info(
                f"Processing data for NOAA location: {loc_name} (mapped to {mapped_location})"
            )

            # Loop through all datasets
            for dataset in self.dataset_map.keys():
                logger.info(f"Pulling {dataset} data for {mapped_location}")

                try:
                    # Fetch data (fetch handles pagination)
                    raw_data = self.fetch(
                        mapped_location, dataset, start_datetime, end_datetime
                    )

                    if raw_data:
                        # Process and store data
                        times, values = self.process(raw_data, mapped_location, dataset)

                        if times and values:
                            self.store(
                                times, values, loc_name, dataset
                            )  # Use original location name for storage
                            logger.info(
                                f"Successfully stored {len(times)} records for {loc_name} - {dataset}"
                            )
                            success_count += 1
                        else:
                            logger.warning(
                                f"No data points processed for {loc_name} - {dataset}"
                            )
                            error_count += 1
                    else:
                        logger.warning(
                            f"No raw data fetched for {loc_name} - {dataset}"
                        )
                        error_count += 1

                except Exception as e:
                    logger.error(f"Error processing {dataset} for {loc_name}: {e}")
                    error_count += 1

        logger.info(
            f"NOAA data pull completed. Success: {success_count}, Errors: {error_count}"
        )
        return True
