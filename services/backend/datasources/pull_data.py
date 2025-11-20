#!/usr/bin/env python3
"""
Entry point script for pulling data from various sources.
This can be run as a standalone script or imported and used programmatically.
"""

import argparse
import logging
import sys
from datetime import datetime

from services.backend.datasources.manager import DataSourceManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to console
        logging.FileHandler("data_pull.log"),  # Log to file
    ],
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Pull data from various sources.")
    parser.add_argument(
        "--all", action="store_true", help="Pull all data from all sources"
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Name of specific source to pull data from (e.g., 'usgs', 'noaa')",
    )
    parser.add_argument(
        "--location",
        type=str,
        help="Name of specific location to pull data for (e.g., 'Bismarck')",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to pull data for (default: 30)",
    )

    args = parser.parse_args()

    if not (args.all or args.source or args.location):
        parser.print_help()
        return

    # Create the data source manager
    manager = DataSourceManager()

    start_time = datetime.now()
    logger.info(f"Starting data pull at: {start_time}")

    if args.all:
        logger.info(f"Pulling all data for the last {args.days} days")
        manager.pull_all_data(args.days)
    elif args.source:
        logger.info(
            f"Pulling data from source '{args.source}' for the last {args.days} days"
        )
        manager.pull_source(args.source, args.days)
    elif args.location:
        logger.info(
            f"Pulling data for location '{args.location}' for the last {args.days} days"
        )
        manager.pull_location(args.location, args.days)

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Data pull completed at: {end_time}")
    logger.info(f"Total duration: {duration}")


if __name__ == "__main__":
    main()
