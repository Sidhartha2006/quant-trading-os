import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

INPUT_FILE = Path("data/processed/XAUUSDT-5m-with-signals.csv")

START = "2026-06-01"
END = "2026-06-05"

df = pd.read_csv(INPUT_FILE, parse_dates=["open_time"])
window = df[(df["open_time"] >= START) & (df["open_time"] < END)].copy()

buys = window[window["signal"] == "BUY"]
sells = window[window["signal"] == "SELL"]

plt.figure(figsize=(16, 8))
plt.plot(window["open_time"], window["close"], color="gray", linewidth=1, label="Close price")
plt.scatter(buys["open_time"], buys["close"], color="green", marker="^", s=80, label="BUY signal", zorder=5)
plt.scatter(sells["open_time"], sells["close"], color="red", marker="v", s=80, label="SELL signal", zorder=5)

plt.title(f"XAUUSDT 5m — Signals from {START} to {END}")
plt.xlabel("Time")
plt.ylabel("Price")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()

OUTPUT_FILE = Path("data/processed/signals_chart.png")
plt.savefig(OUTPUT_FILE, dpi=150)
print(f"Saved chart to {OUTPUT_FILE}")