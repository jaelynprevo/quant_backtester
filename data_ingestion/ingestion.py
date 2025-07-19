#ingestion.py

import os
import requests
import pandas as pd
from sqlalchemy import create_engine
from datetime import date, datetime, time, timedelta
import time


API_KEY = os.getenv("API_KEY")
DB_URL  = os.getenv("DB_URL")

if not API_KEY or not DB_URL:
    raise RuntimeError("API_KEY and DB_URL must be set in the environment")

def fetch_agg_bars(symbol, start_dt, end_dt, multiplier=1, timespan="minute", limit=5000):
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{symbol}"
        f"/range/{multiplier}/{timespan}/{start_dt}/{end_dt}"
    )
    while True:
        r = requests.get(url, params={
            "adjusted": "true",
            "sort":     "asc",
            "limit":    limit,
            "apiKey":   API_KEY
        })
        if r.status_code == 429:
            # get backoff seconds from header or default to 60
            wait = int(r.headers.get("Retry-After", 60))
            print(f"Rate limited, sleeping for {wait}s…")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json().get("results", [])

def fetch_data(symbol, start_date, end_date):
    all_bars = []
    cur = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    # page in 30‑day chunks to respect the 50k‑row limit
    while cur < end:
        chunk_end = min(cur + timedelta(days=30), end)
        bars = fetch_agg_bars(
            symbol,
            cur.strftime("%Y-%m-%d"),
            chunk_end.strftime("%Y-%m-%d"),
        )
        all_bars.extend(bars)
        time.sleep(12)
        cur = chunk_end + timedelta(days=1)

    df = pd.DataFrame(all_bars)
    # convert timestamps & rename columns
    df["timestamp"] = pd.to_datetime(df.pop("t"), unit="ms")
    df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"}, inplace=True)
    return df

def save_to_db(df, table="btc_minute_bars"):
    engine = create_engine(DB_URL)
    df.to_sql(table, engine, if_exists="append", index=False)

if __name__=="__main__":
    symbol    = "AAPL"
    end       = date.today()
    start     = end - timedelta(days=365*2)
    table     = "aapl_minute_bars"

    df = fetch_data(symbol, start.isoformat(), end.isoformat())
    save_to_db(df, table)
    print(f"Loaded {len(df)} rows for {symbol} from {start} to {end}")
