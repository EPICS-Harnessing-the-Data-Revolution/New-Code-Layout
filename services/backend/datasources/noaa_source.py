import logging
import os
from datetime import datetime, date

import requests
import time

from services.backend.datasources.config import NOAA
from services.backend.datasources.base2 import DataSource
from services.backend.sqlclasses import updateDictionary

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class NOAADataSource(DataSource):
    def __init__(self, start_date=None, format=None):
        # base2.DataSource expects (source, start_date, format)
        super().__init__("NOAA", start_date, format)
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
        }
        # Map from constants.NOAA location names to self.location_dict keys
        self.location_name_mapping = {
            "Bismarck": "Bismarck, ND",
            "Minot": "Minot, ND",
            "Williston/Basin": "Williston, ND",
            # Extended approximations to nearest supported GHCND stations
            "Tioga": "Williston, ND",
            "Stanley": "Minot, ND",
            "Sidney/Richland": "Williston, ND",
            "Watford City": "Williston, ND",
            "Garrison": "Minot, ND",
            "Glendive/Dawson": "Williston, ND",
            "Hazen/Mercer": "Bismarck, ND",
            "Beach": "Williston, ND",
            "Dickinson/Roosevelt": "Williston, ND",
            "Glen": "Williston, ND",
            "Miles City/Wiley": "Williston, ND",
            "Baker": "Williston, ND",
            "Bowman": "Williston, ND",
            "Hettinger": "Williston, ND",
            "Linton": "Bismarck, ND",
            "Buffalo/Harding": "Bismarck, ND",
            "Mobridge": "Bismarck, ND",
            "Faith": "Bismarck, ND",
            "Spearfish/Clyde": "Bismarck, ND",
            "Pierre": "Bismarck, ND",
            "Custer": "Bismarck, ND",
            "Rapid City": "Bismarck, ND",
            "Philip": "Bismarck, ND",
        }
        self.api_base_url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
        # Token from env with provided fallback
        self.api_token = os.getenv(
            "NOAA_API_TOKEN", "WkaDdDnFDuEUpiUEFiNMFcLcNKVsQgtp"
        )
        # Holder for pulled raw payloads and processed series
        self.data = []
        self.processed = []

    def _pull(self):
        """
        Pull raw NOAA data for all configured locations/datasets from cutoff to today.
        Stores raw payloads in self.data.
        """
        self.data = []
        start_dt = self.cutoff.date() if isinstance(self.cutoff, datetime) else date.today()
        end_dt = date.today()

        headers = {"token": self.api_token}

        for loc_name in NOAA:
            mapped_location = self.location_name_mapping.get(loc_name)
            if not mapped_location or mapped_location not in self.location_dict:
                logger.warning(f"Skipping unmapped location: {loc_name}")
                continue

            station_id = self.location_dict[mapped_location]
            for dataset_name, datatype_id in self.dataset_map.items():
                params = {
                    "datasetid": "GHCND",
                    "stationid": station_id,
                    "datatypeid": datatype_id,
                    "startdate": start_dt.strftime("%Y-%m-%d"),
                    "enddate": end_dt.strftime("%Y-%m-%d"),
                    "units": "standard",
                    "limit": 1000,
                    "offset": 0,
                    "includemetadata": "true",
                }

                all_results = []
                logger.info(
                    f"Fetching NOAA data for {mapped_location} ({datatype_id}) from {params['startdate']} to {params['enddate']}"
                )

                backoff_seconds = 1
                while True:
                    try:
                        response = requests.get(self.api_base_url, headers=headers, params=params)
                        response.raise_for_status()
                        payload = response.json()
                        results = payload.get("results", [])
                        if not results:
                            break
                        all_results.extend(results)
                        metadata = payload.get("metadata", {}).get("resultset", {})
                        count = metadata.get("count")
                        offset = metadata.get("offset")
                        limit = metadata.get("limit", params["limit"]) or params["limit"]
                        # If metadata is present, use it; otherwise, fall back to length-based pagination
                        if isinstance(count, int) and isinstance(offset, int) and isinstance(limit, int):
                            if (offset + limit) >= count:
                                break
                            params["offset"] += limit
                        else:
                            # Fallback: if we received less than limit rows, we're done
                            if len(results) < params["limit"]:
                                break
                            params["offset"] += params["limit"]
                        # light throttle between pages
                        time.sleep(0.25)
                    except requests.exceptions.HTTPError as e:
                        status = getattr(getattr(e, 'response', None), 'status_code', None)
                        retry_after = getattr(getattr(e, 'response', None), 'headers', {}).get('Retry-After') if getattr(e, 'response', None) else None
                        if status == 429:
                            sleep_for = int(retry_after) if retry_after and str(retry_after).isdigit() else backoff_seconds
                            logger.warning(f"Rate limited by NOAA (429). Sleeping {sleep_for}s and retrying...")
                            time.sleep(sleep_for)
                            backoff_seconds = min(backoff_seconds * 2, 60)
                            continue
                        logger.error(f"HTTP error {status} fetching NOAA data for {mapped_location} ({datatype_id}): {e}")
                        break
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Error fetching NOAA data for {mapped_location} ({datatype_id}): {e}")
                        break

                self.data.append(
                    {
                        "loc_key": loc_name,  # original constants.NOAA name
                        "mapped_location": mapped_location,
                        "dataset": dataset_name,
                        "datatypeid": datatype_id,
                        "results": all_results,
                    }
                )
                # light throttle between dataset requests
                time.sleep(0.25)

    def _process(self):
        """
        Process self.data into time/value series per (location, dataset).
        Stores results in self.processed.
        """
        self.processed = []
        for entry in self.data:
            raw_data = entry.get("results", [])
            loc_key = entry.get("loc_key")
            dataset_name = entry.get("dataset")

            times = []
            values = []

            needs_scaling = dataset_name in [
                "Average Temperature",
                "Max Temperature",
                "Min Temperature",
                "Precipitation",
            ]
            scaling_factor = 10.0 if needs_scaling else 1.0

            for record in raw_data:
                try:
                    if not isinstance(record, dict):
                        continue
                    timestamp_str = record.get("date")
                    value_val = record.get("value")
                    if timestamp_str and value_val is not None:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        # filter by cutoff if provided
                        if isinstance(self.cutoff, datetime) and timestamp <= self.cutoff:
                            continue
                        processed_value = float(value_val) / scaling_factor
                        times.append(timestamp)
                        values.append(processed_value)
                except Exception as e:
                    logger.error(f"Error processing record for {loc_key} - {dataset_name}: {e}")

            # Ensure chronological order
            if times:
                paired = sorted(zip(times, values), key=lambda x: x[0])
                times, values = [t for t, _ in paired], [v for _, v in paired]

            self.processed.append(
                {
                    "location": loc_key,
                    "dataset": dataset_name,
                    "times": times,
                    "values": values,
                }
            )

    def _push(self):
        """
        Push processed series into SQL using updateDictionary.
        """
        for series in self.processed:
            times = series.get("times", [])
            values = series.get("values", [])
            location = series.get("location")
            dataset = series.get("dataset")
            if times and values:
                updateDictionary(times, values, location, dataset, "noaa_weather")
                logger.info(f"Stored {len(times)} records for {location} - {dataset}")
