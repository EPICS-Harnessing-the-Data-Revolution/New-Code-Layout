#!/usr/bin/env python3
"""Test runner for `services.backend.custom_graph`.

Usage:
  python tools/test_custom_graph.py

What it does:
- Picks a sample location and metric (Hazen / Gauge Height)
- Determines a recent 30-day window (based on DB latest timestamp when available)
- Calls `custom_graph.query_data` to retrieve a DataFrame
- If data exists, calls `export_interactive_html_plotly` to write a standalone HTML file and opens it in the default browser
- Prints diagnostic messages if DB/tables/data are missing

This is a lightweight manual test helper — run from the repo root with your virtualenv active.
"""

import os
import sys
import sqlite3
import tempfile
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

# Ensure repository root is on sys.path so `from services...` works when
# running this script directly (e.g. `python tools/test_custom_graph.py`).
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

try:
    from services.backend import custom_graph
    from services.backend.datasources.config import LOCATION_TO_TABLE, SQL_CONVERSION
except Exception as e:
    print("ERROR: could not import project modules. Make sure you run this from the repo root with the venv activated.")
    print(e)
    raise


def main():
    # Sample choices (modify as needed)
    location = 'Hazen'
    data_name = 'Gauge Height'

    table = LOCATION_TO_TABLE.get(location, 'gauge')
    col = SQL_CONVERSION.get(data_name, data_name.replace(' ', '_').lower())

    print(f"Testing location={location}, table={table}, column={col}")

    # Choose DB path from custom_graph if available, fallback to Measurements.db
    db_path = getattr(custom_graph, 'DB_PATH', None) or 'Measurements.db'
    print('Using DB path:', db_path)

    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        print('WARNING: Measurements DB not found or empty. Aborting test.')
        return

    conn = sqlite3.connect(db_path)
    try:
        # If custom_graph exposes get_latest_datetime, use it to pick a window
        start_e = None
        end_e = None
        if hasattr(custom_graph, 'get_latest_datetime'):
            try:
                latest_dt = custom_graph.get_latest_datetime(conn, table, col)
                if latest_dt:
                    end_e = int(latest_dt.timestamp())
                    start_e = end_e - 30 * 24 * 3600
                    print('Using latest timestamp from DB:', latest_dt)
            except Exception as e:
                print('Could not determine latest datetime via custom_graph.get_latest_datetime():', e)

        if start_e is None or end_e is None:
            # fallback: use last 30 days ending now
            now_ts = int(datetime.now().timestamp())
            end_e = now_ts
            start_e = now_ts - 30 * 24 * 3600
            print('Falling back to last 30 days window')

        print('Query window epochs:', start_e, end_e)

        # Query data
        try:
            df = custom_graph.query_data(conn, table, start_e, end_e)
        except Exception as e:
            print('Error querying data:', e)
            return

        if df is None or df.empty:
            print('No data returned for the selected window. DataFrame empty.')
            return

        print(f'Retrieved {len(df)} rows. Preparing interactive plot...')

        # Write interactive HTML using the helper
        tmpf = tempfile.NamedTemporaryFile(prefix='graph_', suffix='.html', delete=False)
        tmpf.close()
        out_path = tmpf.name

        try:
            custom_graph.export_interactive_html_plotly(df, 'datetime', col, out_path)
            print('Wrote interactive HTML to:', out_path)
            webbrowser.open('file://' + os.path.abspath(out_path))
        except Exception as e:
            print('Failed to export interactive HTML (plotly may be missing):', e)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
