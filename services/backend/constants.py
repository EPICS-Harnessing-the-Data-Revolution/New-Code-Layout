"""
Database constants and configuration values.
"""

# Database file path
import os
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "New-Code-Layout 14-19-29-956", "Measurements.db")

# Location lists by data source type
GAUGES = (
    "Hazen",
    "Stanton",
    "Washburn",
    "Price",
    "Bismarck",
    "Schmidt",
    "Judson",
    "Breien",
    "Mandan",
    "Cash",
    "Wakpala",
    "Whitehorse",
    "Little Eagle",
)

DAMS = ("Fort Peck", "Garrison", "Oahe", "Big Bend", "Fort Randall", "Gavins Point")

MESONETS = ("Carson", "Fort Yates", "Linton", "Mott")

COCORAHS = ("Bison", "Faulkton", "Bismarck", "Langdon")

NOAA = (
    "Williston/Basin",
    "Tioga",
    "Stanley",
    "Minot",
    "Sidney/Richland",
    "Watford City",
    "Garrison",
    "Glendive/Dawson",
    "Hazen/Mercer",
    "Beach",
    "Dickinson/Roosevelt",
    "Glen",
    "Bismarck",
    "Miles City/Wiley",
    "Baker",
    "Bowman",
    "Hettinger",
    "Linton",
    "Buffalo/Harding",
    "Mobridge",
    "Faith",
    "Spearfish/Clyde",
    "Pierre",
    "Custer",
    "Rapid City",
    "Philip",
)

SHADEHILL = ("Shadehill",)

# SQL field mappings for variable names
SQL_CONVERSION = {
    "Elevation": "elevation",
    "Air Temperature": "air_temp",
    "Water Temperature": "water_temp",
    "Flow Spill": "flow_spill",
    "Flow Powerhouse": "flow_power",
    "Flow Out": "flow_out",
    "Tailwater Elevation": "tail_ele",
    "Energy": "energy",
    "Discharge": "discharge",
    "Gauge Height": "gauge_height",
    "Average Air Temperature": "avg_air_temp",
    "Average Relative Humidity": "avg_rel_hum",
    "Average Bare Soil Temperature": "avg_bare_soil_temp",
    "Average Turf Soil Temperature": "avg_turf_soil_temp",
    "Maximum Wind Speed": "max_wind_speed",
    "Average Wind Direction": "avg_wind_dir",
    "Total Solar Radiation": "total_solar_rad",
    "Total Rainfall": "total_rainfall",
    "Average Baromatric Pressure": "avg_bar_pressure",
    "Average Dew Point": "avg_dew_point",
    "Average Wind Chill": "avg_wind_chill",
    "Precipitation": "precipitation",
    "Snowfall": "snowfall",
    "Snow Depth": "snow_depth",
    "Reservoir Storage Content": "res_stor_content",
    "Reservoir Forebay Elevation": "res_forebay_elev",
    "Daily Mean Computed Inflow": "daily_mean_comp_inflow",
    "Daily Mean Air Temperature": "daily_mean_air_temp",
    "Daily Minimum Air Temperature": "daily_min_air_temp",
    "Daily Maximum Air Temperature": "daily_max_air_temp",
    "Total Precipitation (inches per day)": "tot_precip_daily",
    "Total Water Year Precipitation": "tot_year_precip",
    "Daily Mean Total Discharge": "daily_mean_tot_dis",
    "Daily Mean River Discharge": "daily_mean_river_dis",
    "Daily Mean Spillway Discharge": "daily_mean_spill_dis",
    "Daily Mean Gate One Opening": "daily_mean_gate_opening",
    "temperature": "temperature",
    "dewpoint": "dew_point",
    "relativeHumidity": "rel_humidity",
    "windChill": "wind_chill",
    "Average Temperature": "avg_temp",
    "Max Temperature": "max_temp",
    "Min Temperature": "min_temp",
    # Water Quality Parameters
    "Phosphorus (Total) (P)": "total_phosphorus",
    "Phosphorus (Total Kjeldahl) (P)": "total_kjeldahl_phosphorus",
    "Nitrate + Nitrite (N)": "nitrate_nitrite",
    "Nitrate Forms Check": "nitrate_forms_check",
    "Nitrate + Nitrite (N) Dis": "nitrate_nitrite_dissolved",
    "Nitrogen (Total Kjeldahl)": "total_kjeldahl_nitrogen",
    "Nitrogen (TKN-Dissolved)": "tkn_dissolved",
    "Nitrogen (Total-Dis)": "total_nitrogen_dissolved",
    "E.coli": "e_coli",
    "Nitrogen (Total)": "total_nitrogen",
    "pH": "ph",
    "Ammonia (N)": "ammonia_nitrogen",
    "Ammonia (N)-Dissolved": "ammonia_nitrogen_dissolved",
    "Ammonia Forms Check": "ammonia_forms_check",
    "Diss Ammonia TKN Check": "diss_ammonia_tkn_check",
    "Dissolved Phosphorus as P": "dissolved_phosphorus",
}

# Mapping of station IDs to location names
LOCATION_DICT = {
    "6340500": "Hazen",
    "6342500": "Bismarck",
    "6349700": "Schmidt",
    "6348300": "Judson",
    "6349000": "Mandan",
    "6354000": "Breien",
    "06354881": "Wakpala",
    "06357800": "Little Eagle",
    "06356500": "Cash",
    "06360500": "Whitehorse",
}

# Table schema definitions
TABLE_SCHEMAS = {
    "mesonet": """
        CREATE TABLE IF NOT EXISTS mesonet(
            location TEXT, 
            datetime TEXT,
            avg_air_temp REAL, 
            avg_rel_hum REAL,
            avg_bare_soil_temp REAL, 
            avg_turf_soil_temp REAL,
            max_wind_speed REAL, 
            avg_wind_dir REAL,
            total_solar_rad REAL, 
            total_rainfall REAL,
            avg_bar_pressure REAL, 
            avg_dew_point REAL,
            avg_wind_chill REAL, 
            PRIMARY KEY(location, datetime)
        )
    """,
    "gauge": """
        CREATE TABLE IF NOT EXISTS gauge(
            location TEXT, 
            datetime TEXT,
            elevation REAL, 
            gauge_height REAL, 
            discharge REAL, 
            water_temp REAL,
            PRIMARY KEY(location, datetime)
        )
    """,
    "dam": """
        CREATE TABLE IF NOT EXISTS dam(
            location TEXT, 
            datetime TEXT,
            elevation REAL, 
            flow_spill REAL, 
            flow_power REAL,
            flow_out REAL, 
            tail_ele REAL, 
            energy REAL, 
            water_temp REAL,
            air_temp REAL, 
            PRIMARY KEY(location, datetime)
        )
    """,
    "cocorahs": """
        CREATE TABLE IF NOT EXISTS cocorahs(
            location TEXT, 
            datetime TEXT,
            precipitation REAL, 
            snowfall REAL,
            snow_depth REAL, 
            PRIMARY KEY(location, datetime)
        )
    """,
    "shadehill": """
        CREATE TABLE IF NOT EXISTS shadehill(
            location TEXT, 
            datetime TEXT,
            res_stor_content REAL, 
            res_forebay_elev REAL,
            daily_mean_comp_inflow REAL, 
            daily_mean_air_temp REAL,
            daily_min_air_temp REAL, 
            daily_max_air_temp REAL,
            tot_precip_daily REAL, 
            tot_year_precip REAL,
            daily_mean_tot_dis REAL, 
            daily_mean_river_dis REAL,
            daily_mean_spill_dis REAL,
            daily_mean_gate_opening REAL, 
            PRIMARY KEY(location, datetime)
        )
    """,
    "noaa_weather": """
        CREATE TABLE IF NOT EXISTS noaa_weather(
            location TEXT,
            datetime TEXT,
            avg_temp REAL,      -- Corresponds to TAVG
            max_temp REAL,      -- Corresponds to TMAX
            min_temp REAL,      -- Corresponds to TMIN
            precipitation REAL, -- Corresponds to PRCP
            PRIMARY KEY(location, datetime)
        )
    """,
    "water_quality": """
        CREATE TABLE IF NOT EXISTS water_quality(
            location TEXT,
            datetime TEXT,
            total_phosphorus REAL,
            total_kjeldahl_phosphorus REAL,
            nitrate_nitrite REAL,
            nitrate_forms_check REAL,
            nitrate_nitrite_dissolved REAL,
            total_kjeldahl_nitrogen REAL,
            tkn_dissolved REAL,
            total_nitrogen_dissolved REAL,
            e_coli REAL,
            total_nitrogen REAL,
            ph REAL,
            ammonia_nitrogen REAL,
            ammonia_nitrogen_dissolved REAL,
            ammonia_forms_check REAL,
            diss_ammonia_tkn_check REAL,
            dissolved_phosphorus REAL,
            PRIMARY KEY(location, datetime)
        )
    """,
}

# Generate mapping of locations to their table types
LOCATION_TO_TABLE = {}

# Fill in the location to table mapping
for location in GAUGES:
    LOCATION_TO_TABLE[location] = "gauge"
for location in DAMS:
    LOCATION_TO_TABLE[location] = "dam"
for location in MESONETS:
    LOCATION_TO_TABLE[location] = "mesonet"
for location in COCORAHS:
    LOCATION_TO_TABLE[location] = "cocorahs"
for location in NOAA:
    LOCATION_TO_TABLE[location] = "noaa_weather"
for location in SHADEHILL:
    LOCATION_TO_TABLE[location] = "shadehill"
