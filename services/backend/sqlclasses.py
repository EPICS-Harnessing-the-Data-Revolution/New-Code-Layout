import logging
import sqlite3
from datetime import datetime

from constants import (
    DB_PATH,
    LOCATION_TO_TABLE,
    SQL_CONVERSION,
    TABLE_SCHEMAS,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global connection and cursor (consider connection pooling for higher concurrency)
conn = None
cursor = None


def _get_db_connection():
    """Establishes and returns a database connection."""
    global conn, cursor
    if conn is None:
        try:
            logger.info(f"Connecting to database at {DB_PATH}")
            conn = sqlite3.connect(
                DB_PATH, check_same_thread=False
            )  # Allow connection usage across threads if needed, but be cautious
            cursor = conn.cursor()
            _initialize_tables()  # Ensure tables exist on first connection
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            conn = None  # Reset on error
            cursor = None
            raise  # Re-raise the exception to signal failure
    return conn, cursor


def _initialize_tables():
    """Creates tables if they don't exist using schemas from constants."""
    global conn, cursor
    if not conn or not cursor:
        logger.error("Cannot initialize tables without a database connection.")
        return
    try:
        for table_name, schema in TABLE_SCHEMAS.items():
            logger.debug(f"Ensuring table '{table_name}' exists.")
            cursor.execute(schema)
        conn.commit()
        logger.info("Database tables initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error initializing tables: {e}")
        conn.rollback()  # Rollback changes on error


def updateDictionary(
    times: list = None,
    values: list = None,
    location: str = None,
    dataset: str = None,
    data_type: str = None,
):
    """
    Stores or updates time-series data in the appropriate SQL table.

    Args:
        times: A list of datetime objects or strings representing the timestamps.
        values: A list of numerical values corresponding to the times.
        location: The name of the location (e.g., 'Bismarck').
        dataset: The name of the dataset (e.g., 'Air Temperature').
        data_type: The type of data source, used to determine the table name (e.g., 'gauge', 'dam').
    """
    if not all([times, values, location, dataset, data_type]):
        logger.warning("Missing data for updateDictionary. Skipping database update.")
        return

    if len(times) != len(values):
        logger.error(
            f"Mismatch between number of timestamps ({len(times)}) and values ({len(values)}) for {location} - {dataset}. Skipping update."
        )
        return

    # Get the correct SQL column name for the dataset
    sql_field = SQL_CONVERSION.get(dataset)
    if not sql_field:
        logger.error(
            f"No SQL field mapping found for dataset '{dataset}'. Skipping update."
        )
        return

    # Get the correct table name based on data_type or location mapping
    table_name = data_type  # Use data_type directly as the table name
    # Alternative: Use LOCATION_TO_TABLE if data_type isn't reliable
    # table_name = LOCATION_TO_TABLE.get(location)
    # if not table_name:
    #     logger.error(f"No table mapping found for location '{location}'. Skipping update.")
    #     return

    if table_name not in TABLE_SCHEMAS:
        logger.error(
            f"Invalid table name '{table_name}' derived from data_type '{data_type}'. Not found in TABLE_SCHEMAS. Skipping update."
        )
        return

    try:
        conn, cursor = _get_db_connection()
        if not conn or not cursor:
            logger.error("Failed to get database connection. Skipping update.")
            return

        logger.info(
            f"Updating table '{table_name}' for location '{location}', dataset '{dataset}' ({sql_field}) with {len(times)} records."
        )

        data_to_insert = []
        for i, timestamp in enumerate(times):
            # Ensure timestamp is in the correct string format 'YYYY-MM-DD HH:MM:SS'
            if isinstance(timestamp, datetime):
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(timestamp, str):
                # Attempt to parse and reformat if it's a string, assuming ISO or similar format
                try:
                    dt_obj = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    )  # Handle 'Z' for UTC
                    formatted_time = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # If parsing fails, assume it's already in the desired format or log a warning
                    logger.warning(
                        f"Could not parse timestamp string '{timestamp}'. Assuming 'YYYY-MM-DD HH:MM:SS' format."
                    )
                    formatted_time = timestamp  # Use as is, hoping it's correct
            else:
                logger.warning(
                    f"Unsupported timestamp type '{type(timestamp)}'. Skipping record."
                )
                continue

            value = values[i]
            # Handle potential None values if necessary, though process should ideally filter these
            if value is None:
                logger.debug(
                    f"Skipping record with None value at time {formatted_time} for {location} - {dataset}"
                )
                continue

            data_to_insert.append((location, formatted_time, value))

        if not data_to_insert:
            logger.info("No valid data points to insert after formatting/validation.")
            return

        # Use INSERT OR REPLACE to handle existing records (based on PRIMARY KEY)
        # The primary key is typically (location, datetime)
        sql = f"INSERT OR REPLACE INTO {table_name} (location, datetime, {sql_field}) VALUES (?, ?, ?)"

        cursor.executemany(sql, data_to_insert)
        conn.commit()
        logger.info(
            f"Successfully updated {len(data_to_insert)} records in '{table_name}' for {location} - {dataset}."
        )

    except sqlite3.Error as e:
        logger.error(f"Database error during update for {location} - {dataset}: {e}")
        if conn:
            conn.rollback()  # Rollback changes on error
    except Exception as e:
        logger.error(f"Unexpected error during database update: {e}")
        if conn:
            conn.rollback()


# Optional: Function to close the connection when the application exits
def close_db_connection():
    global conn
    if conn:
        logger.info("Closing database connection.")
        conn.close()
        conn = None


# Example of how to ensure connection closure (e.g., using atexit)
# import atexit
# atexit.register(close_db_connection)
