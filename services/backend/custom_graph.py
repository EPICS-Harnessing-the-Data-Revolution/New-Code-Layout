"""
custom_graph.py
Safely query Measurements.db and plot one selected variable over time.
Automatically finds Measurements.db at the repository root.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys
import pathlib

# --- CONFIG ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def find_repo_root(start_dir, repo_name="New-Code-Layout"):
    """Go up folders until we find the repo root."""
    current = start_dir
    while True:
        if os.path.basename(current) == repo_name:
            return current
        parent = os.path.dirname(current)
        if parent == current:  # reached root of filesystem
            return None
        current = parent

def find_database(repo_root, db_name="Measurements.db"):
    """Search for Measurements.db in the repo root."""
    db_path = os.path.join(repo_root, db_name)
    if os.path.exists(db_path):
        return db_path
    return None

# --- Locate repository root ---
REPO_ROOT = find_repo_root(SCRIPT_DIR)
if not REPO_ROOT:
    print("ERROR: Could not determine repository root.")
    sys.exit(1)

DB_PATH = find_database(REPO_ROOT)
if not DB_PATH:
    print(f"ERROR: Could not find Measurements.db at repo root: {REPO_ROOT}")
    sys.exit(1)

print(f"\nFound database at: {DB_PATH}")

# -----------------------
# Helper functions
# -----------------------

def list_tables(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [r[0] for r in cur.fetchall()]

def list_columns(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    return [r[1] for r in cur.fetchall()]

def detect_time_format(df):
    if df.empty:
        return "string"
    first_val = df['datetime'].iloc[0]
    try:
        int(first_val)
        return 'epoch'
    except (ValueError, TypeError):
        return 'string'

def query_data(conn, table, start_epoch, end_epoch):
    df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 1;", conn)
    fmt = detect_time_format(df)

    if fmt == 'epoch':
        query = f"SELECT * FROM {table} WHERE datetime BETWEEN ? AND ?"
        df = pd.read_sql_query(query, conn, params=(start_epoch, end_epoch))
        df['datetime'] = pd.to_datetime(df['datetime'], unit='s', errors='coerce')
    else:
        start_dt = datetime.fromtimestamp(start_epoch).strftime("%Y-%m-%d %H:%M:%S")
        end_dt = datetime.fromtimestamp(end_epoch).strftime("%Y-%m-%d %H:%M:%S")
        query = f"SELECT * FROM {table} WHERE datetime BETWEEN ? AND ?"
        df = pd.read_sql_query(query, conn, params=(start_dt, end_dt))
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

    return df

def export_interactive_html_plotly(df, datetime_col, value_col, out_path):
    """
    Create an interactive HTML plot using Plotly and save as a standalone file.
    - df: pandas DataFrame with datetime_col parsed as datetimes
    - datetime_col: name of the datetime column
    - value_col: name of the value column to plot
    - out_path: output HTML filepath
    """
    try:
        import plotly.express as px
    except Exception as e:
        raise RuntimeError("plotly required: pip install plotly") from e

    # ensure datetime is datetime dtype
    df = df.copy()
    df[datetime_col] = pd.to_datetime(df[datetime_col], errors="coerce")
    df = df.dropna(subset=[datetime_col, value_col])

    fig = px.line(df, x=datetime_col, y=value_col, title=f"{value_col} over time")
    fig.update_layout(autosize=True, margin=dict(l=40, r=20, t=50, b=40))
    # write standalone html (include plotly.js from CDN)
    fig.write_html(out_path, full_html=True, include_plotlyjs="cdn")
    return out_path

def export_interactive_html_mpld3(fig, out_path):
    """
    Save a matplotlib Figure as an interactive HTML using mpld3.
    - fig: matplotlib.figure.Figure
    - out_path: output HTML filepath
    """
    try:
        import mpld3
    except Exception as e:
        raise RuntimeError("mpld3 required: pip install mpld3") from e

    mpld3.save_html(fig, out_path)
    return out_path

def ensure_graphs_dir():
    graphs_dir = os.path.join(REPO_ROOT, "static", "graphs")
    os.makedirs(graphs_dir, exist_ok=True)
    return graphs_dir

def _safe_name(s: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s).strip("_")

def save_interactive(df, table, column):
    """
    Try to save an interactive HTML for the dataframe/column.
    Prefer Plotly, fall back to mpld3, otherwise save a PNG and wrap in HTML.
    Returns path to written file.
    """
    out_dir = ensure_graphs_dir()
    fname = f"{_safe_name(table)}_{_safe_name(column)}.html"
    out_path = os.path.join(out_dir, fname)

    # Try Plotly
    try:
        import plotly.express as px
        dff = df.copy()
        dff['datetime'] = pd.to_datetime(dff['datetime'], errors='coerce')
        dff = dff.dropna(subset=['datetime', column])
        fig = px.line(dff, x='datetime', y=column, title=f"{column} - {table}")
        fig.update_layout(autosize=True, margin=dict(l=40, r=20, t=50, b=40))
        fig.write_html(out_path, full_html=True, include_plotlyjs="cdn")
        print(f"Wrote interactive Plotly HTML -> {out_path}")
        return out_path
    except Exception:
        pass

    # Try mpld3
    try:
        import mpld3
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(pd.to_datetime(df['datetime'], errors='coerce'), df[column], marker='o', linestyle='-', markersize=3)
        ax.set_title(f"{column} over time ({table})")
        ax.set_xlabel("Datetime")
        ax.set_ylabel(column)
        ax.grid(True)
        mpld3.save_html(fig, out_path)
        plt.close(fig)
        print(f"Wrote interactive mpld3 HTML -> {out_path}")
        return out_path
    except Exception:
        pass

    # Fallback: save PNG and wrap in basic HTML
    png_name = f"{_safe_name(table)}_{_safe_name(column)}.png"
    png_path = os.path.join(out_dir, png_name)
    try:
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(pd.to_datetime(df['datetime'], errors='coerce'), df[column], marker='o', linestyle='-', markersize=3)
        ax.set_title(f"{column} over time ({table})")
        ax.set_xlabel("Datetime")
        ax.set_ylabel(column)
        ax.grid(True)
        fig.tight_layout()
        fig.savefig(png_path)
        plt.close(fig)
        html = f"<html><body><h2>{column} - {table}</h2><img src=\"{os.path.basename(png_path)}\" alt=\"{column}\"></body></html>"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Wrote fallback HTML with PNG -> {out_path}")
        return out_path
    except Exception as e:
        print(f"Failed to write any output for {table}/{column}: {e}")
        return None

def get_time_format(conn, table: str) -> str:
    """
    Return 'epoch' or 'string' for the table's datetime column.
    Uses the existing detect_time_format helper on a single-row sample.
    """
    try:
        sample = pd.read_sql_query(f"SELECT datetime FROM \"{table}\" LIMIT 1;", conn)
        return detect_time_format(sample)
    except Exception:
        return "string"


def get_latest_datetime(conn, table: str, column: str):
    """
    Return the most recent datetime (as a datetime.datetime) for rows where `column` is not NULL,
    or None if no values exist. Handles epoch and string datetime formats.
    """
    cur = conn.cursor()
    fmt = get_time_format(conn, table)
    try:
        cur.execute(f'SELECT datetime FROM "{table}" WHERE "{column}" IS NOT NULL ORDER BY datetime DESC LIMIT 1')
        row = cur.fetchone()
        if not row or row[0] is None:
            return None
        ts = row[0]
        if fmt == "epoch":
            try:
                return datetime.fromtimestamp(int(ts))
            except Exception:
                return None
        # string formats
        try:
            return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except Exception:
            for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    return datetime.strptime(str(ts), f)
                except Exception:
                    continue
        return None
    except Exception:
        return None


def main():
    """
    Generate interactive Plotly HTML for every table/column in the database.
    For each (table, column) attempt:
      1) produce a 30-day graph ending now
      2) if step 1 has no data, find the most recent timestamp for that column and
         produce a 30-day graph ending at that timestamp
      3) if still no data, fall back to graphing all available rows for that column
    """
    conn = sqlite3.connect(DB_PATH)

    # default 30-day window relative to now
    from datetime import datetime, timedelta

    now = datetime.now()
    default_end = now
    default_start = now - timedelta(days=30)

    out_dir = ensure_graphs_dir()

    tables = list_tables(conn)
    if not tables:
        print("\nERROR: No tables found in this database!")
        conn.close()
        return

    print(f"Found {len(tables)} tables. Generating interactive HTML for 30-day windows (prefers most recent data).")
    total_saved = 0
    total_skipped = 0

    for table in tables:
        # skip internal sqlite tables
        if table.startswith("sqlite_"):
            continue

        try:
            columns = list_columns(conn, table)
        except Exception as e:
            print(f"Skipping table {table} (failed to list columns): {e}")
            total_skipped += 1
            continue

        # ignore metadata columns
        ignored = {"datetime", "location", "rowid", "id"}
        data_columns = [c for c in columns if c.lower() not in ignored]

        if not data_columns:
            print(f"No data columns found in table {table}, skipping.")
            total_skipped += 1
            continue

        # determine time format once per table
        time_fmt = get_time_format(conn, table)

        for column in data_columns:
            # reset window to default
            end_dt = default_end
            start_dt = default_start

            # 1) Try last 30 days ending now
            start_epoch = int(start_dt.timestamp())
            end_epoch = int(end_dt.timestamp())
            try:
                df = query_data(conn, table, start_epoch, end_epoch)
            except Exception as e:
                print(f"Query failed for {table}/{column} ({start_dt} -> {end_dt}): {e}")
                df = pd.DataFrame()

            # keep only relevant column and datetime
            if column in df.columns:
                df = df.loc[:, ["datetime", column]]
                df = df.dropna(subset=["datetime", column])
            else:
                df = pd.DataFrame()  # force fallback below

            # 2) If no data, find the latest datetime for that column and use 30 days ending there
            if df.empty:
                latest = get_latest_datetime(conn, table, column)
                if latest:
                    end_dt = latest
                    start_dt = end_dt - timedelta(days=30)
                    start_epoch = int(start_dt.timestamp())
                    end_epoch = int(end_dt.timestamp())
                    try:
                        df = query_data(conn, table, start_epoch, end_epoch)
                        if column in df.columns:
                            df = df.loc[:, ["datetime", column]]
                            df = df.dropna(subset=["datetime", column])
                        else:
                            df = pd.DataFrame()
                    except Exception as e:
                        print(f"Query failed for {table}/{column} ({start_dt} -> {end_dt}): {e}")
                        df = pd.DataFrame()

            # 3) Final fallback: graph all available non-null rows for column
            if df.empty:
                try:
                    raw = pd.read_sql_query(f'SELECT datetime, "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL ORDER BY datetime ASC', conn)
                    if time_fmt == "epoch":
                        raw["datetime"] = pd.to_datetime(raw["datetime"], unit="s", errors="coerce")
                    else:
                        raw["datetime"] = pd.to_datetime(raw["datetime"], errors="coerce")
                    raw = raw.dropna(subset=["datetime", column])
                    df = raw
                    # set start/end for filename based on data range
                    if not df.empty:
                        start_dt = pd.to_datetime(df["datetime"].iloc[0])
                        end_dt = pd.to_datetime(df["datetime"].iloc[-1])
                except Exception:
                    df = pd.DataFrame()

            if df.empty:
                print(f"No data found for {table}/{column}, skipping.")
                total_skipped += 1
                continue

            # build output filename including actual date range used
            safe_table = _safe_name(table)
            safe_col = _safe_name(column)
            s_str = pd.to_datetime(df["datetime"].iloc[0]).strftime("%Y%m%d")
            e_str = pd.to_datetime(df["datetime"].iloc[-1]).strftime("%Y%m%d")
            fname = f"{safe_table}__{safe_col}__{s_str}_{e_str}_interactive.html"
            out_path = os.path.join(out_dir, fname)

            # export interactive html (Plotly preferred)
            try:
                export_interactive_html_plotly(df, "datetime", column, out_path)
                print(f"WROTE: {out_path}")
                total_saved += 1
            except Exception as e:
                print(f"Failed to export Plotly HTML for {table}/{column}: {e}")
                try:
                    fallback = save_interactive(df, table, column)
                    if fallback:
                        print(f"Fallback wrote: {fallback}")
                        total_saved += 1
                    else:
                        total_skipped += 1
                except Exception as e2:
                    print(f"Fallback also failed for {table}/{column}: {e2}")
                    total_skipped += 1

    conn.close()
    print(f"\nDone. Saved: {total_saved} interactive files. Skipped: {total_skipped}. Outputs in: {out_dir}")

if __name__ == "__main__":
    main()
