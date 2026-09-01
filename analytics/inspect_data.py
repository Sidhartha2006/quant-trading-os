import pandas as pd

# Load the raw CSV
df = pd.read_csv("data/raw/XAUUSDT-1m-2026-08-14.csv")

# Convert timestamps from Unix ms to readable datetime
df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

# Basic checks
print("Rows:", len(df))
print("First candle:\n", df.iloc[0])
print("Last candle:\n", df.iloc[-1])

# Check for duplicate timestamps
dupes = df["open_time"].duplicated().sum()
print("Duplicate timestamps:", dupes)

# Check for missing minutes (should be 1440 candles for a full day)
expected = pd.date_range(df["open_time"].iloc[0], df["open_time"].iloc[-1], freq="1min")
missing = expected.difference(df["open_time"])
print("Missing candles:", len(missing))

# Check OHLC sanity (high should be >= open/close/low, etc.)
bad_rows = df[(df["high"] < df["low"]) | (df["high"] < df["open"]) | (df["high"] < df["close"])]
print("Invalid OHLC rows:", len(bad_rows))