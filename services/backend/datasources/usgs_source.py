import requests
import csv
import os
from datetime import datetime, date, timedelta
from services.backend.datasources.base2 import DataSource
from services.backend.datasources.utils import DataParser
from services.backend.sqlclasses import updateDictionary

class USGSDataSource(DataSource):
    """
    Data source for USGS gauge data using base2.DataSource template.
    """

    def __init__(self, start_date=None, format=None):
        super().__init__("USGS", start_date, format)
        self.location_dict = {
            'Hazen': ['06340500', 1],
            'Stanton': ['06340700', 2],
            'Washburn': ['06341000', 2],
            'Price': ['06342020', 2],
            'Bismarck': ['06342500', 3],
            'Schmidt': ['06349700', 2],
            'Judson': ['06348300', 1], 
            'Mandan': ['06349000', 1],
            'Breien': ['06354000', 1]   ,
            'Wakpala': ['06354881', 4],
            'Little Eagle': ['06357800', 4],
            'Cash': ['06356500', 4],
            'Whitehorse': ['06360500', 4]
        }
        self.data = []
        self.processed = []

    def _pull(self):
        """
        Pull raw USGS data for all locations from cutoff to today. Store in self.data.
        """
        self.data = []
        start_dt = self.cutoff.date() if isinstance(self.cutoff, datetime) else date.today()
        end_dt = date.today()

        for location, (code, category) in self.location_dict.items():
            # Configure per-category URL parts
            if category == 1:
                query = 'cb_00060=on&cb_00065=on&cb_63160=on'
                num_sets = 3
                linecount = 56
            elif category == 2:
                query = 'cb_00065=on&cb_63160=on'
                num_sets = 2
                linecount = 54
            elif category == 3:
                query = 'cb_00010=on&cb_00060=on&cb_00065=on&cb_63160=on'
                num_sets = 4
                linecount = 58
            else:
                query = 'cb_00060=on&cb_00065=on'
                num_sets = 2
                linecount = 54

            linecount2 = linecount + 3
            combined_matrix = []

            # Chunk the date range to avoid server truncation (60-day chunks)
            chunk_start = start_dt
            while chunk_start <= end_dt:
                chunk_end = min(chunk_start + timedelta(days=60), end_dt)
                s_year, s_month, s_day = chunk_start.year, f"{chunk_start.month:02d}", f"{chunk_start.day:02d}"
                e_year, e_month, e_day = chunk_end.year, f"{chunk_end.month:02d}", f"{chunk_end.day:02d}"

                url = (
                    f'https://waterdata.usgs.gov/nwis/uv?{query}&format=rdb&site_no={code}'
                    f'&legacy=1&period=&begin_date={s_year}-{s_month}-{s_day}&end_date={e_year}-{e_month}-{e_day}'
                )

                response = requests.get(url)

                data_file = f"./temp_data.txt"
                with open(data_file, "w") as f:
                    writer = csv.writer(f)
                    for line in response.text.split("\n"):
                        writer.writerow(line.split("\t"))

                data_lines = []
                count = 0
                alternate = 0
                with open(data_file, "r") as file:
                    for line in file:
                        if count == linecount:
                            data_lines.append(line)
                        elif count > linecount2:
                            if alternate % 2 == 0:
                                line = line.strip('\n')
                                data_lines.append(line)
                            alternate += 1
                        count += 1

                tmp_csv = f"./temp_{location}.csv"
                with open(tmp_csv, "w") as file:
                    for line in data_lines:
                        file.write(f"{line}")

                with open(tmp_csv, 'rt') as f:
                    reader = csv.reader(f)
                    matrix_chunk = list(reader)

                try:
                    os.remove(tmp_csv)
                    os.remove(data_file)
                except Exception:
                    pass

                # Drop last row if empty and extend combined
                if matrix_chunk and matrix_chunk[-1] == []:
                    matrix_chunk = matrix_chunk[:-1]
                combined_matrix.extend(matrix_chunk)

                # Advance chunk
                chunk_start = chunk_end + timedelta(days=1)

            self.data.append({
                'location': location,
                'data_matrix': combined_matrix,
                'category': category,
                'num_sets': num_sets
            })
    
    def _process(self):
        """
        Transform self.data into standardized series and store in self.processed.
        """
        self.processed = []
        for entry in self.data:
            data_matrix = entry.get('data_matrix')
            category = entry.get('category')
            num_sets = entry.get('num_sets')
            location = entry.get('location')

            if not data_matrix:
                continue

            if num_sets == 2:
                length = 8
            elif num_sets == 3:
                length = 10
            else:
                length = 12

            times = []
            dataset1 = []
            dataset2 = []
            dataset3 = []
            dataset4 = []

            for matrixindex in range(4, len(data_matrix)):
                try:
                    for idx in range(0, length):
                        if idx == 2:
                            times.append(data_matrix[matrixindex][idx])
                        elif idx == 4:
                            dataset1.append(data_matrix[matrixindex][idx])
                        elif idx == 6:
                            dataset2.append(data_matrix[matrixindex][idx])
                        elif num_sets >= 3 and idx == 8:
                            dataset3.append(data_matrix[matrixindex][idx])
                        elif num_sets == 4 and idx == 10:
                            dataset4.append(data_matrix[matrixindex][idx])
                except IndexError:
                    continue

            datasets = {}
            if category == 1:
                datasets = {
                    "Elevation": dataset1,
                    "Discharge": dataset2,
                    "Gauge Height": dataset3,
                }
                if location == 'Judson':
                    datasets = {
                        "Elevation": dataset1,
                        "Gauge Height": dataset2,
                        "Discharge": dataset3,
                    }
            elif category == 2:
                datasets = {"Elevation": dataset1, "Gauge Height": dataset2}
            elif category == 3:
                datasets = {
                    "Elevation": dataset1,
                    "Water Temperature": dataset2,
                    "Discharge": dataset3,
                    "Gauge Height": dataset4,
                }
            elif category == 4:
                datasets = {"Discharge": dataset1, "Gauge Height": dataset2}

            if "Discharge" in datasets:
                discharge = datasets["Discharge"]
                for i in range(len(discharge)):
                    if discharge[i] == 'Ice':
                        discharge[i] = 0

            for ds_name, values in datasets.items():
                parsed_values = DataParser.parse_numeric_list(values)
                self.processed.append({
                    'location': location,
                    'dataset': ds_name,
                    'times': times,
                    'values': parsed_values,
                })
    
    def _push(self):
        """
        Push processed series into SQL using updateDictionary for 'gauge' table.
        """
        for series in self.processed:
            times = series.get('times') or []
            values = series.get('values') or []
            location = series.get('location')
            dataset = series.get('dataset')
            if times and values:
                updateDictionary(times, values, location, dataset, 'gauge')