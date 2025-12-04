"""
Populate Measurements.db with sample data for testing.
Creates tables from `services.backend.datasources.config.TABLE_SCHEMAS` and inserts a few recent rows
for several locations (Hazen/gauge, Fort Peck/dam, Carson/mesonet, Bison/cocorahs, Bismarck/noaa_weather, Shadehill/shadehill).

Run from repo root: `python tools/populate_measurements_db.py`
"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import os

# Ensure imports work when running from repo root
repo_root = Path(__file__).resolve().parents[1]
import sys
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from services.backend.datasources import config

DB_PATH = config.DB_PATH
print('Using DB_PATH =', DB_PATH)

# Create DB directory if needed
db_dir = os.path.dirname(DB_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Create tables using provided schemas
for tname, ddl in config.TABLE_SCHEMAS.items():
    print('Creating table', tname)
    cur.executescript(ddl)

# Helper to format datetime strings
def fmt(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')

now = datetime.utcnow()
rows = []

# gauge: Hazen
rows.append(("gauge", (
    ('Hazen', fmt(now - timedelta(days=1)), 100.0, 5.5, 200.0, 12.3),
    ('Hazen', fmt(now - timedelta(days=10)), 100.0, 5.2, 190.0, 11.8),
)))

# dam: Fort Peck
rows.append(("dam", (
    ('Fort Peck', fmt(now - timedelta(days=2)), 150.0, 10.0, 123.4, 50.0, 48.0, 1.1, 9.9, 7.2),
    ('Fort Peck', fmt(now - timedelta(days=12)), 150.0, 9.5, 120.0, 49.0, 47.5, 1.0, 9.5, 7.0),
)))

# mesonet: Carson
rows.append(("mesonet", (
    ('Carson', fmt(now - timedelta(days=3)), 15.2, 65.0, 12.0, 11.5, 5.5, 180.0, 200.0, 1012.0, 2.3),
    ('Carson', fmt(now - timedelta(days=20)), 14.8, 64.0, 11.7, 11.0, 4.0, 170.0, 0.0, 1010.5, 1.8),
)))

# cocorahs: Bison
rows.append(("cocorahs", (
    ('Bison', fmt(now - timedelta(days=4)), 0.12, 0.0, 0.0),
    ('Bison', fmt(now - timedelta(days=14)), 0.00, 0.0, 0.0),
)))

# noaa_weather: Bismarck
rows.append(("noaa_weather", (
    ('Bismarck', fmt(now - timedelta(days=5)), 2.3, 5.0, -1.0, 0.1),
    ('Bismarck', fmt(now - timedelta(days=15)), 1.8, 4.5, -2.0, 0.0),
)))

# shadehill
rows.append(("shadehill", (
    ('Shadehill', fmt(now - timedelta(days=6)), 10000.0, 1800.0, 500.0, 8.0, 3.0, 12.0, 0.2, 1.5, 400.0, 380.0, 350.0, 0.5),
)))

# Insert rows using parameterized queries
for tname, recs in rows:
    print(f'Inserting into {tname}: {len(recs)} rows')
    if tname == 'gauge':
        q = 'INSERT OR REPLACE INTO gauge(location, datetime, elevation, gauge_height, discharge, water_temp) VALUES (?, ?, ?, ?, ?, ?)'
    elif tname == 'dam':
        q = 'INSERT OR REPLACE INTO dam(location, datetime, elevation, flow_spill, flow_power, flow_out, tail_ele, energy, water_temp, air_temp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    elif tname == 'mesonet':
        q = 'INSERT OR REPLACE INTO mesonet(location, datetime, avg_air_temp, avg_rel_hum, avg_bare_soil_temp, avg_turf_soil_temp, max_wind_speed, total_solar_rad, total_rainfall, avg_bar_pressure, avg_dew_point) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    elif tname == 'cocorahs':
        q = 'INSERT OR REPLACE INTO cocorahs(location, datetime, precipitation, snowfall, snow_depth) VALUES (?, ?, ?, ?, ?)'
    elif tname == 'noaa_weather':
        q = 'INSERT OR REPLACE INTO noaa_weather(location, datetime, avg_temp, max_temp, min_temp, precipitation) VALUES (?, ?, ?, ?, ?, ?)'
    elif tname == 'shadehill':
        q = 'INSERT OR REPLACE INTO shadehill(location, datetime, res_stor_content, res_forebay_elev, daily_mean_comp_inflow, daily_mean_air_temp, daily_min_air_temp, daily_max_air_temp, tot_precip_daily, tot_year_precip, daily_mean_tot_dis, daily_mean_river_dis, daily_mean_spill_dis, daily_mean_gate_opening) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    else:
        print('No insert handler for table', tname)
        continue

    for rec in recs:
        try:
            cur.execute(q, rec)
        except Exception as e:
            print('Failed to insert into', tname, rec, e)

conn.commit()
conn.close()
print('Populated Measurements.db with sample data.')
