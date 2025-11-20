# Base.py
Here’s the full documentation for your `DataSource` class in Markdown format, ready to be included in a `README.md` or other documentation files:

---

## `DataSource` Abstract Base Class

The `DataSource` class defines a standardized interface for pulling, processing, and storing data from external sources such as APIs, CSVs, or other datasets. This base class is designed to be subclassed, with the core methods `fetch` and `process` required to be implemented.

---

### Class Definition

```python
class DataSource(ABC)
```

#### Attributes

- **`name`** (`str`):  
  The name of the data source (e.g., `"NOAA"`, `"NDGIS"`).

- **`data_type`** (`str`):  
  The category of data this source provides (e.g., `"weather"`, `"economic"`, `"geospatial"`).

---

### Methods

#### `__init__(self, name, data_type)`

Initializes the `DataSource` instance.

##### Parameters:

- `name` (`str`): The name of the data source.
- `data_type` (`str`): The type of data this source provides.

---

#### `fetch(self, location=None, dataset=None, start_date=None, end_date=None)`

Abstract method to fetch raw data from the external source.

##### Parameters:

- `location` (`str`, optional): Location to fetch data for (geographic or logical).
- `dataset` (`str`, optional): Specific dataset or variable.
- `start_date` (`date` or `str`, optional): Start of the data range.
- `end_date` (`date` or `str`, optional): End of the data range.

#### Returns:

- `Any`: Raw data from the source.

---

#### `process(self, raw_data=None, location=None, dataset=None)`

Abstract method to process raw data into a structured format.

##### Parameters:

- `raw_data` (`Any`): Raw data as returned from `fetch()`.
- `location` (`str`, optional): Location name or identifier.
- `dataset` (`str`, optional): Dataset name or identifier.

##### Returns:

- `Tuple[List[datetime], List[Any]]`:  
  A tuple of timestamps and corresponding data values.

---

#### `store(self, data, times=None, values=None, location=None, dataset=None, conn=None)`

Stores processed data into a database.

##### Parameters:

- `data` (`Any`): Processed data (can be unused if `times` and `values` are given).
- `times` (`List[datetime]`, optional): List of datetime objects for each data point.
- `values` (`List[Any]`, optional): Values corresponding to the timestamps.
- `location` (`str`, optional): Location identifier.
- `dataset` (`str`, optional): Dataset identifier.
- `conn` (`Any`, optional): Database connection object.

##### Raises:

- `ValueError`: If no valid connection is provided.

---

#### `pull(self, location=None, dataset=None, start_date=None, end_date=None)`

Pulls data from the source, processes it, and stores it using the internal logic.

##### Parameters:

- `location` (`str`, optional): Target location for the data.
- `dataset` (`str`, optional): Dataset name or type.
- `start_date` (`date` or `str`, optional): Start date for data retrieval.
- `end_date` (`date` or `str`, optional): End date for data retrieval.

##### Returns:

- `Tuple[List[datetime], List[Any]]`:  
  A tuple containing the timestamps and values after processing.

---

### Optional Method Placeholder

#### `pull_all(self, start_date, end_date)`

*Currently commented out.*  
This can be implemented to support pulling **all available datasets** or **all locations** over a given date range.

---

### Example Usage (Subclassing)

```python
class WeatherDataSource(DataSource):
    def fetch(self, location, dataset, start_date, end_date):
        # Implementation to fetch weather data
        pass

    def process(self, raw_data, location, dataset):
        # Process raw weather data into timestamps and values
        return times, values
```



# Manager.py
Here's the complete Markdown documentation for the `DataSourceManager` class with proper structure, suitable for inclusion in a technical documentation file or `README.md`:

---

## `DataSourceManager` Class

The `DataSourceManager` class coordinates data pulling and storage from multiple registered data sources. It acts as a centralized interface for interacting with external data APIs, organizing them by source name and associated locations.

---

### Purpose

> **"Manager class for coordinating all data sources.  
> Provides a single point of access for pulling data from multiple sources."**

---

## Initialization

```python
manager = DataSourceManager()
```

Initializes all supported data source classes and maps their associated locations using constants such as `GAUGES`, `DAMS`, etc.

---

## Attributes

- **`sources`** (`Dict[str, DataSource]`):  
  Dictionary mapping source names to their corresponding initialized data source objects.

- **`location_sets`** (`Dict[str, List[str]]`):  
  Maps each source name to a list of its available locations.

---

## Methods

### `pull_all_data(self, num_days=30)`

Pulls and stores data from **all** data sources for the last `num_days`.

#### Parameters:

- `num_days` (`int`, default `30`): Number of past days to include in the data range.

#### Output:

Prints logs of progress and completion per source.

---

### `pull_source(self, source_name, num_days=30)`

Pulls and stores data from a **specific source** over the last `num_days`.

#### Parameters:

- `source_name` (`str`): The key name of the data source (e.g., `'noaa'`, `'usgs'`).
- `num_days` (`int`, default `30`): Number of past days to include in the data range.

#### Output:

Prints start, end dates, and logs for data retrieval and error handling.

---

### `pull_location(self, location, num_days=30)`

Pulls data for a **specific location** over the last `num_days`.  
Automatically determines which data source and datasets the location belongs to.

#### Parameters:

- `location` (`str`): Target location identifier.
- `num_days` (`int`, default `30`): Number of past days to include in the data range.

#### Output:

Prints logs for each dataset pulled and stored for the location, grouped by source.

---

### `_pull_dataset(self, source, location, dataset, start_date, end_date)`

Private helper function to fetch, process, and store a single dataset for a given location.

#### Parameters:

- `source` (`DataSource`): Data source instance.
- `location` (`str`): Location to pull data for.
- `dataset` (`str`): Dataset/variable name.
- `start_date` (`dict`): Start date in dictionary form `{year, month, day}`.
- `end_date` (`dict`): End date in dictionary form `{year, month, day}`.

#### Output:

Prints status of each dataset's retrieval and storage success or failure.

---

### `get_source(self, source_name)`

Returns the source object corresponding to the given name.

#### Parameters:

- `source_name` (`str`): Key name of the data source.

#### Returns:

- `DataSource` or `None`: The corresponding data source object, or `None` if not found.

---

### `list_sources(self)`

Lists all registered source keys.

#### Returns:

- `List[str]`: Names of all available sources.

---

### `list_locations(self, source_name=None)`

Lists available locations for a given source or for all sources if `None`.

#### Parameters:

- `source_name` (`str`, optional): Specific source to filter locations for.

#### Returns:

- `Dict[str, List[str]]`: Dictionary of locations mapped to source(s).

---

### `store_all(self, data)`

**(Stub)** Placeholder method for storing all data in the database.

#### Parameters:

- `data` (`Any`): Data to be stored.

--

# NDMES_source.py

## `NDMESDataSource` Class

The `NDMESDataSource` class is a concrete implementation of the `DataSource` abstract base class, used to fetch, process, and store hourly mesonet weather data from the North Dakota Mesonet (NDAWN) API.

---

### Purpose

> Provides structured access to weather station data from North Dakota’s Mesonet for a defined time period and location.

---

## Initialization

```python
ndmes = NDMESDataSource()
```

Initializes the data source with predefined Mesonet station mappings for the following locations:
- Fort Yates
- Linton
- Mott
- Carson

---

## Attributes

- **`location_dict`** (`dict`):  
  Maps location names to their corresponding station codes and descriptive labels used in the NDAWN API.

---

## Methods

### `fetch(self, location, dataset=None, start_date=None, end_date=None)`

Fetches raw CSV data from the NDAWN API for a specific location and date range.

#### Parameters:
- `location` (`str`): One of the supported locations in `location_dict`.
- `dataset` (`str`, optional): Not used directly in the fetch call.
- `start_date` (`str`): Start date in `YYYYMMDD` format.
- `end_date` (`str`): End date in `YYYYMMDD` format.

#### Returns:
- `pandas.DataFrame`: Parsed CSV data as a DataFrame.
- Returns `None` on error or if HTTP request fails.

---

### `process(self, raw_data, location, dataset)`

Processes the raw mesonet DataFrame into a standardized format with timestamped values.

#### Parameters:
- `raw_data` (`pd.DataFrame`): The raw data fetched from NDAWN.
- `location` (`str`): Location name used for logging.
- `dataset` (`str`): Desired weather metric to extract.

#### Returns:
- `Tuple[List[str], List[float]]`:  
  A list of timestamps and a list of numeric values.
- Returns `([], [])` if data is unavailable or dataset is not found.

---

### `pull_all(self, start_date, end_date)`

Pulls and stores all available datasets for all known locations over the specified date range.

#### Parameters:
- `start_date` (`str`): Start date in `YYYYMMDD` format.
- `end_date` (`str`): End date in `YYYYMMDD` format.

#### Returns:
- `dict`: Nested dictionary structured as:
  ```json
  {
    "Fort Yates": {
        "Average Air Temperature": {
            "times": [...],
            "values": [...]
        },
        ...
    },
    ...
  }
  ```

---

## Supported Datasets

The following datasets can be pulled and processed:

- `Average Air Temperature`
- `Average Relative Humidity`
- `Average Bare Soil Temperature`
- `Average Turf Soil Temperature`
- `Maximum Wind Speed`
- `Average Wind Direction`
- `Total Solar Radiation`
- `Total Rainfall`
- `Average Baromatric Pressure`
- `Average Dew Point`
- `Average Wind Chill`

---


# CoCoRaHS_source.py
Here’s the complete **Markdown documentation** for your `CoCoRaHSDataSource` class:

---

### `CoCoRaHSDataSource` Class

The `CoCoRaHSDataSource` class provides access to precipitation and snow data from the **Community Collaborative Rain, Hail & Snow Network (CoCoRaHS)**. It implements the `DataSource` abstract base class, allowing for uniform fetching, processing, and storing of weather observation data.

---

#### Purpose

> Fetches, processes, and stores precipitation, snowfall, and snow depth data from CoCoRaHS for supported stations across the Dakotas.

---

### Initialization

```python
cocoRah = CoCoRaHSDataSource()
```

Initializes the data source with a dictionary of predefined CoCoRaHS station IDs and metadata.

---

### Attributes

- **`station_dict`** (`dict`):  
  Maps location names to a list containing:
  - CoCoRaHS station ID (e.g., `"SDFK0006"`)
  - Earliest available date for that station
  - Internal name used for database storage (e.g., `"Bison"`)

---

### Methods

#### `fetch(self, location=None, dataset=None, start_date=None, end_date=None)`

Fetches raw data for a specific location and time period from the RCC ACIS API.

##### Parameters:

- `location` (`str`): Location key from `station_dict`.
- `dataset` (`str`, optional): Dataset name (not used in fetching, only in processing).
- `start_date` (`str`, optional): Ignored for now; earliest date from dictionary is used.
- `end_date` (`str`, optional): Used to define how recent the data should be (default: today).

##### Returns:

- `dict`: Parsed JSON data from API.
- `None` if the fetch fails.

---

#### `process(self, raw_data, location, dataset)`

Processes JSON data into standardized timestamp and value lists.

##### Parameters:

- `raw_data` (`dict`): Data returned from `fetch()`.
- `location` (`str`): Location key from `station_dict`.
- `dataset` (`str`): One of `"Precipitation"`, `"Snowfall"`, or `"Snow Depth"`.

##### Returns:

- `Tuple[List[str], List[float]]`:  
  - List of timestamps in the format `YYYY-MM-DD 00:00:00`.
  - List of float values or `None` if data is missing.

---

#### `pull_all(self, start_date, end_date)`

Pulls and stores **all datasets** for **all available stations**.

##### Parameters:

- `start_date` (`str`): Not currently used.
- `end_date` (`str | dict`): End date for data range, in either `YYYYMMDD` format or as a `dict` with keys `year`, `month`, `day`.

##### Behavior:

- For each station:
  - Fetches the latest data.
  - Parses and stores `"Precipitation"`, `"Snowfall"`, and `"Snow Depth"`.

---

#### `get_link(self, station_id, start_date, end_date)`

Generates a URL to query RCC ACIS data for a specific station and time range.

##### Returns:

- `str`: API endpoint URL.

---

#### `change_time_string_ACIS(self, date_str)`

Converts a date in `YYYY-MM-DD` format to a standard timestamp.

##### Returns:

- `str`: Timestamp string in the format `YYYY-MM-DD 00:00:00`.

---

#### `store(self, data, times=None, values=None, location=None, dataset=None, conn=None)`

Stores the processed data in a SQLite database (`measurement.db`).

> ⚠️ Currently, this method only establishes a connection and cursor but does not execute insert statements.

---

## Datasets Supported

- `Precipitation`
- `Snowfall`
- `Snow Depth`

---

# NOAA_source.py

# Shadehill_source.py
Here’s the complete **Markdown documentation** for your `ShadehillDataSource` class, formatted for inclusion in project documentation or a README:

---

## `ShadehillDataSource` Class

The `ShadehillDataSource` class is a concrete implementation of the `DataSource` abstract class. It is used for retrieving and processing reservoir and weather data for the Shadehill Reservoir from the U.S. Bureau of Reclamation's ArcRead API.

---

### Purpose

> This class automates fetching historical daily reservoir and atmospheric measurements from Shadehill using HTTP form submissions and parses the plain-text responses into a structured format.

---

## Initialization

```python
shadehill = ShadehillDataSource()
```

Creates an instance of the data source and initializes supported dataset mappings.

---

## Attributes

- **`datasets`** (`dict`):  
  Maps dataset codes (used in API requests) to human-readable names.  
  Example:
  - `"AF"` → `"Reservoir Storage Content"`
  - `"MX"` → `"Daily Maximum Air Temperature"`
  - `"PP"` → `"Total Precipitation (inches per day)"`

---

## Methods

### `fetch(self, location, dataset=None, start_date=None, end_date=None)`

Submits a POST request to the Shadehill ArcRead API to retrieve raw data for a specific dataset and date range.

#### Parameters:
- `location` (`str`): Always `"Shadehill"` (not used in URL).
- `dataset` (`str`): Dataset code (e.g., `"AF"`, `"MX"`, etc.).
- `start_date` (`dict`): Start date as a dictionary with keys `year`, `month`, `day`.
- `end_date` (`dict`): End date in the same dictionary format.

#### Returns:
- `str`: Raw plain-text response from the server.
- `None`: On network error or invalid status.

---

### `process(self, raw_data, location, dataset)`

Parses the raw text response into a structured format with timestamps and numerical values.

#### Parameters:
- `raw_data` (`str`): Raw data returned from `fetch`.
- `location` (`str`): Always `"Shadehill"`.
- `dataset` (`str`): Dataset code (used to reverse-map to the full name if needed).

#### Returns:
- `Tuple[List[str], List[float]]`:  
  A tuple of:
  - List of datetime strings (`YYYY-MM-DD 00:00`)
  - List of corresponding values (floats or `None` for invalid entries)

---

### `pull_all(self, start_date, end_date)`

Pulls **all supported datasets** for Shadehill between the given start and end dates, and stores them using the parent `store()` method.

#### Parameters:
- `start_date` (`dict`): Dictionary with `year`, `month`, `day`.
- `end_date` (`dict`): Dictionary with `year`, `month`, `day`.

#### Output:
- Prints progress for each dataset retrieved and stored.

---

## Example Usage

```python
if __name__ == "__main__":
    shadehill = ShadehillDataSource()
    
    start = DateHelper.string_to_list("20210624")  # {'year': 2021, 'month': 6, 'day': 24}
    end = DateHelper.string_to_list("20230401")    # {'year': 2023, 'month': 4, 'day': 1}

    shadehill.pull_all(start, end)
```

---

## Supported Dataset Codes

| Code | Name                                 |
|------|--------------------------------------|
| `AF` | Reservoir Storage Content            |
| `FB` | Reservoir Forebay Elevation          |
| `IN` | Daily Mean Computed Inflow           |
| `MM` | Daily Mean Air Temperature           |
| `MN` | Daily Minimum Air Temperature        |
| `MX` | Daily Maximum Air Temperature        |
| `PP` | Total Precipitation (inches/day)     |
| `PU` | Total Water Year Precipitation       |
| `QD` | Daily Mean Total Discharge           |
| `QRD`| Daily Mean River Discharge           |
| `QSD`| Daily Mean Spillway Discharge        |
| `RAD`| Daily Mean Gate One Opening          |

---

# USACE_source.py
Here is the full **Markdown documentation** for the `USACEDataSource` class:

---

## `USACEDataSource` Class

The `USACEDataSource` class provides access to dam-related hydrological data from the **U.S. Army Corps of Engineers (USACE)**. It implements the `DataSource` base class to fetch, process, and store data for major dams along the Missouri River.

---

#### Purpose

> Automates downloading and parsing daily operational data (e.g., elevation, flows, temperatures) from USACE for key reservoir sites using publicly available tabular data.

---

### Initialization

```python
usace = USACEDataSource()
```

Creates an instance of the data source with a predefined mapping of dam locations and associated codes.

---

### Attributes

- **`location_dict`** (`dict`):  
  Maps dam names to their associated USACE data codes:
  ```python
  {
      'Fort Peck': ['FTPK'],
      'Garrison': ['GARR'],
      'Oahe': ['OAHE'],
      'Big Bend': ['BEND'],
      'Fort Randall': ['FTRA'],
      'Gavins Point': ['GAPT']
  }
  ```

---

### Methods

#### `fetch(self, location, dataset, start_date=None, end_date=None)`

Fetches the raw plain-text tabular data from the USACE site for a specified dam location.

##### Parameters:

- `location` (`str`): Name of the dam.
- `dataset` (`str`): Not used (included for compatibility).
- `start_date` (`str`, optional): Not used.
- `end_date` (`str`, optional): Not used.

##### Returns:

- `str`: Cleaned raw text content.
- `None`: If the request fails.

##### Notes:

- Creates a temporary `.txt` file to store response and parse line-wise.
- Automatically deletes the temporary file after processing.

---

#### `process(self, raw_data, location, dataset)`

Parses the raw dam data into timestamped values for a given dataset.

##### Parameters:

- `raw_data` (`str`): Raw tabular string returned by `fetch`.
- `location` (`str`): Location name.
- `dataset` (`str`): One of the supported datasets.

##### Returns:

- `Tuple[List[str], List[float]]`:  
  A tuple of:
  - List of datetime strings (`YYYY-MM-DD HH:MM`)
  - List of values (`float`), or `None` for invalid entries.

##### Datasets Available:
- `"Elevation"`
- `"Flow Spill"`
- `"Flow Powerhouse"`
- `"Flow Out"`
- `"Tailwater Elevation"`
- `"Energy"`
- `"Water Temperature"`
- `"Air Temperature"`

---

#### `pull_all(self, start_date, end_date)`

Pulls and stores all supported datasets for all dam locations.

##### Parameters:

- `start_date` (`str`): Not used.
- `end_date` (`str`): Not used.

##### Behavior:

- Iterates over all locations.
- Fetches the data once per location.
- Processes and stores values for each supported dataset.

## Dataset Fields Description

| Field               | Description                                |
|---------------------|--------------------------------------------|
| `Elevation`         | Reservoir water surface elevation          |
| `Flow Spill`        | Water flow over spillways                  |
| `Flow Powerhouse`   | Water flow through power generation units  |
| `Flow Out`          | Total water released from the dam          |
| `Tailwater Elevation` | Water elevation below the dam            |
| `Energy`            | Energy generated                           |
| `Water Temperature` | Temperature of water near the dam          |
| `Air Temperature`   | Air temperature above the dam              |

---

# USGS_source.py
Here is the **Markdown documentation** for your `USGSDataSource` class, formatted for use in a README or project doc:

---

## `USGSDataSource` Class

The `USGSDataSource` class interfaces with the **United States Geological Survey (USGS)** website to retrieve and parse real-time hydrologic data from stream gauges across North and South Dakota. It extends the `DataSource` base class and supports various datasets such as discharge, elevation, and temperature.

---

### Purpose

> Automates the collection and processing of gauge height, discharge, water temperature, and elevation data from multiple USGS monitoring sites using direct CSV scraping.

---

## Initialization

```python
usgs = USGSDataSource()
```

Creates an instance of the data source with built-in mappings for several USGS monitoring stations.

---

## Attributes

- **`location_dict`** (`dict`):  
  Maps location names to a list:
  - USGS Site Number
  - Category (used to determine available variables and format):
    - Category 1: 3 datasets
    - Category 2: 2 datasets
    - Category 3: 4 datasets
    - Category 4: 2 datasets

---

## Methods

### `fetch(self, location, dataset, start_date, end_date)`

Fetches raw data from the USGS website in RDB (tab-delimited) format.

#### Parameters:

- `location` (`str`): Site name (must exist in `location_dict`).
- `dataset` (`str`): Ignored (present for compatibility).
- `start_date` (`dict`): `{year, month, day}`
- `end_date` (`dict`): `{year, month, day}`

#### Returns:

- `dict`: Contains:
  - `'data_matrix'`: Cleaned matrix of parsed lines (excluding trailing junk)
  - `'category'`: Category value for the site
  - `'num_sets'`: Number of available datasets

---

### `process(self, raw_data, location, dataset)`

Parses the fetched matrix into usable `time` and `value` lists.

#### Parameters:

- `raw_data` (`dict`): Output from `fetch()`
- `location` (`str`): Name of the USGS site
- `dataset` (`str`): One of the supported dataset names

#### Returns:

- `Tuple[List[str], List[float]]`:  
  List of time strings and corresponding float values

#### Supported Datasets by Category:

| Category | Datasets Available                                            |
|----------|--------------------------------------------------------------|
| 1        | `"Elevation"`, `"Discharge"`, `"Gauge Height"`              |
| 2        | `"Elevation"`, `"Gauge Height"`                             |
| 3        | `"Elevation"`, `"Water Temperature"`, `"Discharge"`, `"Gauge Height"` |
| 4        | `"Discharge"`, `"Gauge Height"`                             |

---

### `pull_all(self, start_date, end_date)`

Pulls all datasets for all locations listed in `location_dict`.

#### Parameters:

- `start_date` (`dict`): Start date in `{year, month, day}`
- `end_date` (`dict`): End date in `{year, month, day}`

#### Behavior:

- Iterates over each location.
- Fetches and processes data for all possible datasets.
- Calls `.store()` to persist values.

---

## Special Handling

- **Discharge values** of `'Ice'` are converted to `0`.
- Temporary files (`.csv`, `.txt`) are created and removed during the fetch step.

---

# Utils.py

# pull_data.py