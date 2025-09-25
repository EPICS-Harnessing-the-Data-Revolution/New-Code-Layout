"""
API Configuration file for data sources.
Set your API tokens here or use environment variables.
"""

import os

# NOAA API Configuration
# Get your free API token from: https://www.ncdc.noaa.gov/cdo-web/token
NOAA_API_TOKEN = os.getenv("NOAA_API_TOKEN", "YOUR_NOAA_TOKEN_HERE")

# USGS API Configuration (usually doesn't require a token)
USGS_API_TOKEN = os.getenv("USGS_API_TOKEN", None)

# Other API configurations can be added here
# Example:
# USACE_API_TOKEN = os.getenv("USACE_API_TOKEN", "YOUR_USACE_TOKEN_HERE")

def get_noaa_token():
    """Get NOAA API token with validation."""
    if NOAA_API_TOKEN == "YOUR_NOAA_TOKEN_HERE":
        print("WARNING: NOAA API token not set!")
        print("Please set the NOAA_API_TOKEN environment variable or update config/api_config.py")
        print("Get your free token from: https://www.ncdc.noaa.gov/cdo-web/token")
        return None
    return NOAA_API_TOKEN

def get_usgs_token():
    """Get USGS API token (usually not required)."""
    return USGS_API_TOKEN

