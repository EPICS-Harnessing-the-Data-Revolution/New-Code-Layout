
# EPICS HDR Organizational Structure
The system follows a hierarchical architecture with the DataSourceManager at the top, coordinating multiple specialized data sources that all inherit from a common DataSource base class. This architecture enables a plug-and-play approach where new data sources can be easily integrated. The base class enforces a consistent interface (fetch, process, store) while allowing each implementation to handle the specifics of their data sources. The manager provides high-level operations (pull_all_data, pull_source, pull_location) that coordinate data acquisition across sources. All data sources ultimately store their processed data in a SQL database through the common store method. The system leverages utility classes for date handling and data parsing, providing shared functionality across all data sources.


## Data Sources File Descriptions
### Base.py: 
Defines the abstract DataSource class that establishes the contract all data sources must follow. It implements a standard data flow pipeline (fetch → process → store) with abstract methods for source-specific operations. The base class handles database interaction, allowing implementations to focus on data acquisition and processing.

### Manager.py: 
Acts as the orchestration layer with the DataSourceManager class that initializes all data sources and maintains mappings of locations to sources. It provides methods to pull data from all sources simultaneously, from a specific source, or for a specific location across relevant sources. The manager handles date range calculations and routes requests to appropriate sources with error handling.

### CoCoRaHS_source.py: 
Implements retrieval of precipitation and snow data from community weather stations, using the ACIS API. It handles four specific locations in the Dakotas, processing three datasets (precipitation, snowfall, snow depth) per location.

### NDMES_source.py: 
Retrieves meteorological data from the North Dakota Mesonet system, handling multiple weather measurements. It uses the NDAWN CSV API to fetch hourly data for four locations, processing eleven different datasets per station.

### NOAA_source.py: 
Fetches weather data from National Oceanic and Atmospheric Administration stations, handling four locations in North Dakota and multiple datasets related to temperature, humidity, and wind chill.

### Shadehill_source.py: 
Specializes in retrieving data specifically for the Shadehill reservoir through the USBR form API. It handles twelve different measurements including water levels, flow rates, temperature, and precipitation.

### USACE_source.py: 
Manages data from six U.S. Army Corps of Engineers dams along the Missouri River. It retrieves and processes eight datasets per dam including elevation, flow measurements, and energy production.

### USGS_source.py: 
The most complex implementation, handling thirteen river gauge locations with varying data structures across four different gauge categories. It processes up to four datasets per location including gauge height, elevation, discharge, and water temperature.

### Utils.py: 
Provides support classes for date operations (DateHelper) and numeric data parsing (DataParser), handling common tasks like date range calculation and conversion of text values to numeric format.

### pull_data.py: 
A script that runs all data sources for time-based interval updating, presumably intended for scheduled execution to keep the database current.



## Database Structure 
Since there are numerous data sources with varied variables and different data types, a large amount of diverse data is involved. To organize this effectively, two tables are used:
- The first table contains all the metadata and links to the data sources.
- The second table includes all of the actual data. The datasets have been joined using an outer join to preserve as many variables as possible.

## Addressing API Failures
API failures are common as the data we work wit h is constantly changing at a varying pace. Some w6ebsites are phased out while others are phased in. With this, the APIs we call, also changes. When an API fails, it's crucial to have a strategy in place for managing the impact and ensuring minimal disruption. Pivoting effectively can mean switching to backup plans, whether that’s through retries, alternative sources, or degraded services.

Retrying with Exponential Backoff: One of the simplest ways to pivot is to implement retry-logic. This ensures that if an API fails, the system will attempt to reconnect after waiting for increasing periods of time. This helps avoid overwhelming the API with repeated requests and allows the system some time to recover before retrying. Exponential backoff is particularly useful in case of temporary outages or rate limiting, as it reduces the frequency of retries over time.

Circuit Breaker Pattern: Another approach to handle API failure is using the circuit breaker pattern. If the system detects that the API is failing repeatedly (e.g., due to server errors), the circuit breaker will open, effectively stopping further requests to that API. This prevents the system from continuing to send requests to an unavailable service, which could worsen the issue. After a set period, the circuit breaker will test the service again, and if successful, the system will resume normal operation. This prevents cascading failures within the system, allowing it to focus on recovery.

Alternative Data Sources: When a critical API fails, having alternative data sources in place can be a lifesaver. This is especially useful when data is critical to the operation of the system. By identifying and integrating secondary or backup APIs, the system can automatically failover to these sources if the primary service is unavailable. This ensures continued data availability and system uptime, but it requires prior planning and testing to ensure data consistency across sources.

Graceful Degradation: In some cases, it may not be possible to retrieve fresh data when an API fails. In these situations, the system should be designed to degrade gracefully. Instead of failing outright or leaving users with no data, the system can serve partial, cached, or stale data as a temporary fallback. This strategy ensures that the user experience is still functional, albeit not as ideal, while the system works to recover from the failure. This is particularly useful for non-critical data or features that can function with outdated information until the API issue is resolved.

Health Checks and Alerts: To pivot quickly when an API fails, it’s essential to have real-time health monitoring and alerting in place. By regularly checking the health of the API (through custom health checks or third-party services), the system can detect failures early and initiate recovery actions, such as switching to alternative data sources or retrying requests. Alerts can notify the development or operations team as soon as an issue is detected, allowing them to investigate the root cause and resolve it before it affects users significantly.

Logging and Analytics: To pivot effectively, the system must also track API failures through comprehensive logging. Detailed logs allow for rapid diagnosis and troubleshooting, helping developers identify whether the failure is due to an external API issue or an internal problem with how requests are being made. By analyzing these logs, teams can also identify patterns and proactively address recurring API issues, reducing the likelihood of failure over time.

Each of these strategies requires careful planning and implementation. By combining them, you can build a robust system capable of maintaining functionality even when APIs fail, ensuring that your services remain reliable and resilient under various failure conditions.

## Repetition in Updated Data
Constantly updating data means that everything we pull is repeated stored. Thus, everytime we update, we keep pulling old data again and again. This is not sustainable as it is inefficient and a waste of resources & time. 

To mitigate this inefficiency, the system can implement a lightweight deduplication mechanism using a dedicated log table. This log table acts as a reference ledger, recording metadata such as source_name, location, date, and optionally dataset_type for each unique data point that has been successfully stored. Before inserting any new records into the main data table, the data source checks the log table to determine whether the data for a given combination already exists. If a match is found, the system skips the insertion. If no match is found, the data is written to the database and the corresponding entry is added to the log. This method avoids modifying start dates or ignoring historical corrections, ensuring that even updated past data can be safely inserted if it has not been previously logged.

In cases where incoming data lacks one or more metadata fields—such as missing location or dataset_type—the system adapts by using the most complete and reliable subset of identifiers available to track duplicates. The log table is designed to support nullable fields, and deduplication logic conditionally adjusts its matching criteria based on which fields are present. To further strengthen the identification process, the system can generate and store a hash of the data payload itself, allowing comparison based on content rather than solely on metadata. This enables the system to detect and prevent redundant inserts even when metadata is incomplete or inconsistent. By combining flexible key matching with optional content hashing, the solution provides a robust and scalable approach that integrates seamlessly into the existing SQL-based architecture with minimal overhead.

# Graph Generation 




## Authors
- [@sinha160](https://www.github.com/sinha160)
- [@Adi2p30edu](https://www.github.com/Adi2p30edu)


