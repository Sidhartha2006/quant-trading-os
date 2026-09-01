import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
OUTPUT_FILE = Path("data/processed/XAUUSDT-1m-combined.csv")

# Grab every CSV in data/raw, sorted by filename (which sorts by date)
files = sorted(RAW_DIR.glob("XAUUSDT-1m-*.csv"))
print(f"Found {len(files)} files")

# Load and stack them all into one big table
dfs = [pd.read_csv(f) for f in files]
combined = pd.concat(dfs, ignore_index=True)

# Convert timestamps
combined["open_time"] = pd.to_datetime(combined["open_time"], unit="ms")
combined["close_time"] = pd.to_datetime(combined["close_time"], unit="ms")

# Sort by time (just in case files weren't perfectly ordered)
combined = combined.sort_values("open_time").reset_index(drop=True)

# Drop exact duplicate timestamps if any exist
before = len(combined)
combined = combined.drop_duplicates(subset="open_time")
after = len(combined)
print(f"Dropped {before - after} duplicate rows")

# Check for gaps across the WHOLE combined range
expected = pd.date_range(combined["open_time"].iloc[0], combined["open_time"].iloc[-1], freq="1min")
missing = expected.difference(combined["open_time"])
print(f"Missing candles across full range: {len(missing)}")

print(f"Total candles: {len(combined)}")
print(f"Date range: {combined['open_time'].iloc[0]} to {combined['open_time'].iloc[-1]}")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
combined.to_csv(OUTPUT_FILE, index=False)
print(f"Saved combined file to {OUTPUT_FILE}")