"""
Small test harness for query_data behavior.
Creates in-memory SQLite tables with three datetime storage formats:
 - epoch seconds (INTEGER)
 - epoch milliseconds (INTEGER)
 - ISO datetime text (TEXT)

Runs a robust `query_data` implementation against each and prints results.
"""
import sqlite3
import pandas as pd
from datetime import datetime


def _is_epoch_value(val):
    try:
        v = int(val)
    except Exception:
        return False, None
    if abs(v) > 10**11:
        return True, 'ms'
    return True, 's'


ALLOWED_TABLES = set()


def query_data(conn, table, start_epoch, end_epoch):
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Table '{table}' is not allowed")

    sample_q = f"SELECT datetime FROM {table} WHERE datetime IS NOT NULL LIMIT 1"
    sample = pd.read_sql_query(sample_q, conn)

    if sample.empty:
        return pd.DataFrame()

    sample_val = sample.iloc[0]['datetime']

    is_epoch, epoch_unit = _is_epoch_value(sample_val)

    if is_epoch:
        start_val = int(start_epoch)
        end_val = int(end_epoch)
        query = f"SELECT * FROM {table} WHERE datetime BETWEEN ? AND ?"
        df = pd.read_sql_query(query, conn, params=(start_val, end_val))
        unit = epoch_unit or 's'
        df['datetime'] = pd.to_datetime(df['datetime'], unit=unit, errors='coerce', utc=True)
    else:
        start_dt = datetime.utcfromtimestamp(int(start_epoch)).strftime("%Y-%m-%d %H:%M:%S")
        end_dt = datetime.utcfromtimestamp(int(end_epoch)).strftime("%Y-%m-%d %H:%M:%S")
        query = f"SELECT * FROM {table} WHERE datetime BETWEEN ? AND ?"
        df = pd.read_sql_query(query, conn, params=(start_dt, end_dt))
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce', utc=True)

    return df


def make_tables(conn):
    cur = conn.cursor()
    # epoch seconds
    cur.execute('CREATE TABLE t_epoch_s (datetime INTEGER, value REAL)')
    cur.execute('INSERT INTO t_epoch_s (datetime, value) VALUES (?, ?)', (1609459200, 1.23))  # 2021-01-01 00:00:00 UTC
    cur.execute('INSERT INTO t_epoch_s (datetime, value) VALUES (?, ?)', (1609545600, 2.34))  # 2021-01-02

    # epoch milliseconds
    cur.execute('CREATE TABLE t_epoch_ms (datetime INTEGER, value REAL)')
    cur.execute('INSERT INTO t_epoch_ms (datetime, value) VALUES (?, ?)', (1609459200000, 3.45))
    cur.execute('INSERT INTO t_epoch_ms (datetime, value) VALUES (?, ?)', (1609545600000, 4.56))

    # ISO text
    cur.execute("CREATE TABLE t_iso (datetime TEXT, value REAL)")
    cur.execute('INSERT INTO t_iso (datetime, value) VALUES (?, ?)', ('2021-01-01 00:00:00', 5.67))
    cur.execute('INSERT INTO t_iso (datetime, value) VALUES (?, ?)', ('2021-01-02 00:00:00', 6.78))
    conn.commit()

    ALLOWED_TABLES.update({'t_epoch_s', 't_epoch_ms', 't_iso'})


def run_tests():
    conn = sqlite3.connect(':memory:')
    make_tables(conn)

    # Test epoch seconds: query for 2021-01-01 to 2021-01-02 inclusive
    start = 1609459200
    end = 1609545600
    print('Testing t_epoch_s (epoch seconds)')
    df_s = query_data(conn, 't_epoch_s', start, end)
    print(df_s)
    assert len(df_s) == 2 or len(df_s) == 2, 'Unexpected row count for t_epoch_s'

    # Test epoch ms: provide start/end in ms
    start_ms = 1609459200000
    end_ms = 1609545600000
    print('\nTesting t_epoch_ms (epoch milliseconds)')
    df_ms = query_data(conn, 't_epoch_ms', start_ms, end_ms)
    print(df_ms)
    assert len(df_ms) == 2, 'Unexpected row count for t_epoch_ms'

    # Test ISO: supply epoch seconds for start/end (function will convert to UTC text)
    print('\nTesting t_iso (ISO text)')
    df_iso = query_data(conn, 't_iso', start, end)
    print(df_iso)
    assert len(df_iso) == 2, 'Unexpected row count for t_iso'

    print('\nAll tests passed')


if __name__ == '__main__':
    run_tests()
