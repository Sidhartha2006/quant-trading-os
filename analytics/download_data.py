import requests
import zipfile
import io
from pathlib import Path
from datetime import date, timedelta

# ---- Settings ----
SYMBOL = "XAUUSDT"
INTERVAL = "1m"
START_DATE = date(2026, 6, 1)   # change this to how far back you want
END_DATE = date(2026, 8, 14)    # change this to your most recent day
RAW_DIR = Path("data/raw")
# -------------------

RAW_DIR.mkdir(parents=True, exist_ok=True)

def daterange(start, end):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)

for day in daterange(START_DATE, END_DATE):
    day_str = day.strftime("%Y-%m-%d")
    filename = f"{SYMBOL}-{INTERVAL}-{day_str}.csv"
    filepath = RAW_DIR / filename

    if filepath.exists():
        print(f"Skipping {day_str} (already downloaded)")
        continue

    url = f"https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/{INTERVAL}/{SYMBOL}-{INTERVAL}-{day_str}.zip"
    print(f"Downloading {day_str}...")

    response = requests.get(url)

    if response.status_code != 200:
        print(f"  -> Not available (status {response.status_code}), skipping")
        continue

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(RAW_DIR)

    print(f"  -> Saved {filename}")

print("Done.")