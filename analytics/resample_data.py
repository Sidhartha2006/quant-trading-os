import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/XAUUSDT-1m-combined.csv")
OUTPUT_FILE = Path("data/processed/XAUUSDT-5m-combined.csv")

df = pd.read_csv(INPUT_FILE, parse_dates=["open_time", "close_time"])
df = df.set_index("open_time")

# Resample: combine every 5 one-minute candles into one 5-minute candle
resampled = df.resample("5min").agg({
    "open": "first",
    "high": "max",
    "low": "min",
    "close": "last",
    "volume": "sum",
    "quote_volume": "sum",
    "count": "sum",
    "taker_buy_volume": "sum",
    "taker_buy_quote_volume": "sum",
})

resampled = resampled.dropna()
resampled = resampled.reset_index()

print(f"5-minute candles: {len(resampled)}")
print(f"Date range: {resampled['open_time'].iloc[0]} to {resampled['open_time'].iloc[-1]}")

resampled.to_csv(OUTPUT_FILE, index=False)
print(f"Saved to {OUTPUT_FILE}")