import pandas as pd

# ============================================================
# MTF STRATEGY V2 - HIGH PROBABILITY FILTER
# ============================================================

INPUT_FILE = "data/processed/XAUUSDT-M1-valid-confirmations.csv"

START_BALANCE = 10000.0
RISK_PERCENT = 0.50
RR = 2.0

# High-probability filters from our analysis
BUY_MAX_BOS_DELAY = 4.0
BUY_MAX_RETEST_DELAY = 1.0

SELL_MAX_BOS_DELAY = 2.0

print("=" * 60)
print("       MTF LIQUIDITY + BOS + RETEST V2")
print("=" * 60)

# ============================================================
# LOAD SIGNALS
# ============================================================

print("\nLoading valid confirmations...")

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=[
        "breakout_time",
        "structure_break_time",
        "retest_time"
    ]
)

print("Valid confirmations loaded:", len(df))

# ============================================================
# APPLY HIGH-PROBABILITY FILTERS
# ============================================================

print("\nApplying probability filters...")

buy_filter = (
    (df["signal"] == "BUY") &
    (df["bos_delay_minutes"] <= BUY_MAX_BOS_DELAY) &
    (df["retest_delay_minutes"] <= BUY_MAX_RETEST_DELAY)
)

sell_filter = (
    (df["signal"] == "SELL") &
    (df["bos_delay_minutes"] <= SELL_MAX_BOS_DELAY)
)

filtered = df[buy_filter | sell_filter].copy()

print("Signals before filtering :", len(df))
print("Signals after filtering  :", len(filtered))

print("\nBUY signals :", buy_filter.sum())
print("SELL signals:", sell_filter.sum())

# ============================================================
# SAVE FILTERED SIGNALS
# ============================================================

OUTPUT_FILE = "data/processed/XAUUSDT-M1-high-probability-signals.csv"

filtered.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSaved filtered signals to:")
print(OUTPUT_FILE)

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("              V2 FILTER SUMMARY")
print("=" * 60)

print("\nBUY:")
print("M30 bullish breakout")
print("+ M1 bullish BOS")
print("+ BOS delay <= 4 minutes")
print("+ retest delay <= 1 minute")

print("\nSELL:")
print("M30 bearish breakout")
print("+ M1 bearish BOS")
print("+ BOS delay <= 2 minutes")

print("\n" + "=" * 60)
print("NEXT STEP")
print("=" * 60)
print("Run the V2 backtest using the filtered signals.")