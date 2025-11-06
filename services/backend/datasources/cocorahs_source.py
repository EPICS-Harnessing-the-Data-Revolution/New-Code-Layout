from json import loads

import requests
from datetime import datetime, date

from services.backend.datasources.base2 import DataSource
from services.backend.datasources.config import COCORAHS_STATIONS
from services.backend.sqlclasses import updateDictionary

class CoCoRaHSDataSource(DataSource):
    """
    Data source for CoCoRaHS precipitation and snow data using base2 template.
    """

    def __init__(self, start_date=None, format=None):
        super().__init__("CoCoRaHS", start_date, format)
        self.station_dict = COCORAHS_STATIONS
        self.data = []
        self.processed = []

    def _pull(self):
        """
        Pull raw CoCoRaHS data for all configured stations from each station's start
        date through today. Stores raw payloads in self.data.
        """
        self.data = []
        end_date_str = date.today().strftime("%Y%m%d")

        for location, station_info in self.station_dict.items():
            station_id = station_info[0]
            start_date_str = station_info[1]
            url = self.get_link(station_id, start_date_str, end_date_str)
            try:
                response = requests.get(url)
                response.raise_for_status()
                results_dict = loads(response.text)
            except Exception as e:
                results_dict = None

            self.data.append({
                'location': location,
                'dict_location': station_info[2] if len(station_info) > 2 else location,
                'raw': results_dict
            })

    def _process(self):
        """
        Process raw CoCoRaHS data in self.data into standardized series.
        Stores series in self.processed.
        """
        self.processed = []
        datasets = {
            'Precipitation': 1,
            'Snowfall': 2,
            'Snow Depth': 3,
        }

        for entry in self.data:
            raw = entry.get('raw') or {}
            data_list = raw.get('data') or []
            location = entry.get('location')
            dict_location = entry.get('dict_location', location)

            # Build time list once
            times_all = []
            for row in data_list:
                if not row:
                    continue
                date_str = row[0]
                # Convert to full datetime string and apply cutoff filter
                ts = self.change_time_string_ACIS(date_str)
                if isinstance(self.cutoff, datetime):
                    try:
                        if datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") <= self.cutoff:
                            times_all.append(None)
                            continue
                    except Exception:
                        pass
                times_all.append(ts)

            for ds_name, idx in datasets.items():
                values = []
                times = []
                for i, row in enumerate(data_list):
                    if not row:
                        continue
                    val = row[idx] if len(row) > idx else None
                    try:
                        v = float(val) if val not in (None, "") else None
                    except Exception:
                        v = None
                    # Keep aligned with time filter
                    t = times_all[i] if i < len(times_all) else None
                    if t is not None and v is not None:
                        times.append(t)
                        values.append(v)

                self.processed.append({
                    'location': dict_location,
                    'dataset': ds_name,
                    'times': times,
                    'values': values,
                })

    def _push(self):
        """
        Push processed series into SQL using updateDictionary for 'cocorahs' table.
        """
        for series in self.processed:
            times = series.get('times') or []
            values = series.get('values') or []
            location = series.get('location')
            dataset = series.get('dataset')
            if times and values:
                updateDictionary(times, values, location, dataset, 'cocorahs')

    # HELPER FUNCTIONS
    def get_link(self, station_id, start_date, end_date):
        """
        Create API URL for data retrieval.
        """

        params = f'{{"sid":"{station_id}","sdate":"{start_date}","edate":"{end_date}","elems":"pcpn,snow,snwd"}}'
        url = f"http://data.rcc-acis.org/StnData?params={params}"
        return url

    def change_time_string_ACIS(self, date_str):
        """
        Convert to database format.

        Input: date_str: Date string in format YYYY-MM-DD

        Returns:
            Formatted datetime string (YYYY-MM-DD HH:MM:SS)
        """
        year, month, day = date_str.split("-")
        return f"{year}-{month}-{day} 00:00:00"
