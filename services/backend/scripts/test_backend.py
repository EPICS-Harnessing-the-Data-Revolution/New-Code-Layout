#!/usr/bin/env python3
"""
Test script to verify the backend functionality.
Tests database connection and the NOAADataSource implementation.
"""

import logging
import os
import sys
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import our modules
from services.backend.database.sqlclaases import _get_db_connection, updateDictionary
from services.backend.datasources.noaa_source import NOAADataSource


def test_database_connection():
    """Test the database connection and initialization."""
    logger.info("Testing database connection...")
    try:
        conn, cursor = _get_db_connection()
        if conn and cursor:
            logger.info("Database connection successful!")

            # Test executing a simple query
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logger.info(f"Tables in the database: {tables}")

            return True
        else:
            logger.error("Failed to get database connection.")
            return False
    except Exception as e:
        logger.error(f"Error during database connection test: {e}")
        return False


def test_noaa_data_source():
    """Test the NOAA data source implementation."""
    logger.info("Testing NOAA data source...")

    # Create the NOAA data source
    try:
        noaa_source = NOAADataSource()

        # Check if API token is configured
        if noaa_source.api_token == "YOUR_DEFAULT_TOKEN":
            logger.warning(
                "NOAA API token not configured. Set the NOAA_API_TOKEN environment variable."
            )
            logger.info(
                "Skipping actual API fetch test. Setting a test token temporarily."
            )
            # Set a temporary token for testing other functionality
            noaa_source.api_token = "test_token"

        # Test the fetch and process methods with a small date range
        location = "Bismarck, ND"
        dataset = "Average Temperature"

        if location not in noaa_source.location_dict:
            logger.error(f"Test location '{location}' not in location_dict.")
            return False

        if dataset not in noaa_source.dataset_map:
            logger.error(f"Test dataset '{dataset}' not in dataset_map.")
            return False

        # Use a very small date range (one day) to minimize API usage
        end_date = datetime.now() - timedelta(days=10)  # 10 days ago
        start_date = end_date - timedelta(days=1)  # Just 1 day range

        logger.info(
            f"Testing fetch method for {location}, {dataset} from {start_date} to {end_date}"
        )

        # Only try to fetch if we have a real token
        if noaa_source.api_token != "test_token":
            raw_data = noaa_source.fetch(location, dataset, start_date, end_date)

            if raw_data is not None:
                logger.info(f"Fetch successful! Got {len(raw_data)} records.")

                # Test the process method
                times, values = noaa_source.process(raw_data, location, dataset)

                if times and values:
                    logger.info(f"Process successful! Processed {len(times)} records.")
                    logger.info(
                        f"First timestamp: {times[0]}, First value: {values[0]}"
                    )
                else:
                    logger.warning("Process returned empty results.")
            else:
                logger.warning(
                    "Fetch returned None. This might be normal if no data exists for the date range."
                )
        else:
            logger.info("Skipping actual API fetch with test token.")

        # Test date conversion for pull_all
        start_date_dict = {"year": "2023", "month": "01", "day": "01"}
        end_date_dict = {"year": "2023", "month": "01", "day": "02"}

        logger.info("Testing pull_all method date conversion...")
        # Call pull_all but catch any exception to prevent actual API calls with test token
        try:
            # Temporarily modify the location_name_mapping to include our test location
            original_mapping = (
                noaa_source.location_name_mapping
                if hasattr(noaa_source, "location_name_mapping")
                else {}
            )
            if not hasattr(noaa_source, "location_name_mapping"):
                noaa_source.location_name_mapping = {}
            noaa_source.location_name_mapping["TestLocation"] = "Bismarck, ND"

            # Mock the fetch method to prevent actual API calls during test
            original_fetch = noaa_source.fetch
            noaa_source.fetch = lambda *args, **kwargs: []

            # Now try to run pull_all
            noaa_source.pull_all(start_date_dict, end_date_dict)
            logger.info("pull_all method executed without errors.")

            # Restore original methods and attributes
            noaa_source.fetch = original_fetch
            if original_mapping:
                noaa_source.location_name_mapping = original_mapping
            else:
                delattr(noaa_source, "location_name_mapping")

        except Exception as e:
            logger.error(f"Error during pull_all test: {e}")
            return False

        return True
    except Exception as e:
        logger.error(f"Error during NOAA data source test: {e}")
        return False


def run_tests():
    """Run all tests."""
    tests = [
        ("Database Connection", test_database_connection),
        ("NOAA Data Source", test_noaa_data_source),
    ]

    success_count = 0
    failure_count = 0

    for test_name, test_func in tests:
        logger.info(f"Running test: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} test passed!")
                success_count += 1
            else:
                logger.error(f"❌ {test_name} test failed!")
                failure_count += 1
        except Exception as e:
            logger.error(f"❌ {test_name} test failed with exception: {e}")
            failure_count += 1

    logger.info(
        f"Test run complete. Successes: {success_count}, Failures: {failure_count}"
    )
    return success_count, failure_count


if __name__ == "__main__":
    logger.info("Starting backend functionality test...")
    success, failure = run_tests()
    sys.exit(1 if failure > 0 else 0)  # Exit with code 1 if any test failed
