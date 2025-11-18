"""
Utility classes and functions for data sources.
"""

from datetime import date, datetime, timedelta


class DateHelper:
    """
    Helper class for date-related operations.
    """

    @staticmethod
    def get_date_range(num_days=30):
        """
        Get start and end dates for a given range.

        Args:
            num_days: Number of days to look back

        Returns:
            Tuple of (start_date, end_date) dictionaries
        """
        # Get the current date
        now = datetime.now()
        end_day = now.strftime("%d")
        end_month = now.strftime("%m")
        end_year = now.strftime("%Y")

        # Get the start date
        start_date_obj = date.today() - timedelta(days=num_days)
        start_day = start_date_obj.strftime("%d")
        start_month = start_date_obj.strftime("%m")
        start_year = start_date_obj.strftime("%Y")

        start_date = {"day": start_day, "month": start_month, "year": start_year}

        end_date = {"day": end_day, "month": end_month, "year": end_year}

        return start_date, end_date

    @staticmethod
    def format_date(date_dict, format_str="%Y-%m-%d"):
        """
        Format a date dictionary into a string.

        Args:
            date_dict: Date dictionary with year, month, day
            format_str: Format string for the output

        Returns:
            Formatted date string
        """
        date_obj = datetime(
            int(date_dict["year"]), int(date_dict["month"]), int(date_dict["day"])
        )
        return date_obj.strftime(format_str)

    @staticmethod
    def format_datetime(date_str, time_str=None):
        """
        Format date and time strings into a standard datetime string.

        Args:
            date_str: Date string (e.g. "2023-01-15")
            time_str: Optional time string (e.g. "13:45")

        Returns:
            Formatted datetime string (e.g. "2023-01-15 13:45:00")
        """
        if time_str:
            return f"{date_str} {time_str}"
        else:
            return f"{date_str} 00:00:00"

    def string_to_list(date):
        year = date[0:4]
        month = date[4:6]
        day = date[6:9]
        return {"year": year, "month": month, "day": day}


class DataParser:
    """
    Helper class for parsing data.
    """

    @staticmethod
    def parse_numeric_list(data_list):
        """
        Parse a list of values into numeric format.

        Args:
            data_list: List of values to parse

        Returns:
            List of parsed numeric values
        """
        result = []

        for item in data_list:
            value = DataParser.parse_numeric(item)
            result.append(value)

        return result

    @staticmethod
    def parse_numeric(value):
        """
        Parse a single value into numeric format.

        Args:
            value: Value to parse

        Returns:
            Parsed numeric value or None if parsing fails or value is special string
        """
        # Convert to string for parsing
        item_str = str(value)

        # Check for special cases - return None for these
        if item_str in ["-", "Ice", "NA", "", "None"]:  # Added more cases
            return None

        # Initialize negative flag
        is_negative = False

        # Remove quotes
        if '"' in item_str:
            item_str = item_str.replace('"', "")

        # Remove commas
        if "," in item_str:
            item_str = item_str.replace(",", "")

        # Check for negative value
        if "-" in item_str:
            is_negative = True
            item_str = item_str.replace("-", "")

        # Strip any remaining whitespace or quotes
        item_str = item_str.strip("\"' ")  # Added space stripping

        # Handle empty string after cleaning
        if not item_str:
            return None

        # Convert to float
        try:
            parsed_value = float(item_str)
            if is_negative:
                parsed_value = -parsed_value
            return parsed_value
        except ValueError:  # Catch specific error
            # Optionally log the error: print(f"Could not parse '{value}' to float.")
            return None
        except Exception as e:  # Catch unexpected errors
            # Optionally log the error: print(f"Unexpected error parsing '{value}': {e}")
            return None
