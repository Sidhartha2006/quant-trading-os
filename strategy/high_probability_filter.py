import pandas as pd
import numpy as np

FILE = "data/processed/mtf_backtest_trades.csv"

df = pd.read_csv(FILE)

print("=" * 70)
print("       HIGH-PROBABILITY TRADE ANALYSIS")
print("=" * 70)

print("\nColumns:")
print(df.columns.tolist())

print("\nTotal trades:", len(df))

# ------------------------------------------------------------
# NORMALIZE RESULT
# ------------------------------------------------------------

result_col = None

for c in ["result", "exit_reason", "outcome", "status"]:
    if c in df.columns:
        result_col = c
        break

if result_col is None:
    print("\nCould not find result column.")
    print("Available columns:", df.columns.tolist())
    raise SystemExit

print("\nResult column:", result_col)

df["WIN"] = (
    df[result_col]
    .astype(str)
    .str.upper()
    .str.contains("TAKE_PROFIT|WIN|TP", regex=True)
)

df["LOSS"] = (
    df[result_col]
    .astype(str)
    .str.upper()
    .str.contains("STOP_LOSS|LOSS|SL", regex=True)
)

# ------------------------------------------------------------
# BASIC PERFORMANCE
# ------------------------------------------------------------

wins = df["WIN"].sum()
losses = df["LOSS"].sum()

print("\n" + "=" * 70)
print("BASELINE")
print("=" * 70)

print("Trades :", len(df))
print("Wins   :", wins)
print("Losses :", losses)

if wins + losses > 0:
    print("Win rate:", round(wins / (wins + losses) * 100, 2), "%")

# ------------------------------------------------------------
# FIND DIRECTION COLUMN
# ------------------------------------------------------------

direction_col = None

for c in ["direction", "signal", "side", "trade_direction"]:
    if c in df.columns:
        direction_col = c
        break

if direction_col:
    print("\n" + "=" * 70)
    print("BUY vs SELL")
    print("=" * 70)

    temp = df.copy()

    temp["SIDE"] = (
        temp[direction_col]
        .astype(str)
        .str.upper()
        .apply(
            lambda x:
            "BUY" if "BUY" in x or "BULL" in x
            else "SELL" if "SELL" in x or "BEAR" in x
            else "OTHER"
        )
    )

    for side in ["BUY", "SELL"]:

        x = temp[temp["SIDE"] == side]

        if len(x) == 0:
            continue

        w = x["WIN"].sum()
        l = x["LOSS"].sum()

        print(
            f"{side:5} | Trades: {len(x):3} | "
            f"Wins: {w:3} | Losses: {l:3} | "
            f"Win Rate: {w / (w+l) * 100:.2f}%"
        )

# ------------------------------------------------------------
# NUMERIC FEATURE ANALYSIS
# ------------------------------------------------------------

features = [
    "bos_delay_minutes",
    "bos_distance",
    "retest_delay_minutes",
    "entry_distance"
]

for feature in features:

    if feature not in df.columns:
        continue

    print("\n" + "=" * 70)
    print(feature.upper())
    print("=" * 70)

    x = df[[feature, "WIN", "LOSS"]].copy()
    x[feature] = pd.to_numeric(x[feature], errors="coerce")
    x = x.dropna()

    if len(x) < 10:
        continue

    # Quantile buckets
    try:
        x["BUCKET"] = pd.qcut(
            x[feature],
            q=4,
            duplicates="drop"
        )
    except:
        continue

    stats = (
        x.groupby("BUCKET", observed=True)
        .agg(
            trades=("WIN", "size"),
            wins=("WIN", "sum"),
            losses=("LOSS", "sum")
        )
    )

    stats["win_rate"] = (
        stats["wins"] /
        (stats["wins"] + stats["losses"]) * 100
    )

    print(stats.round(2).to_string())

# ------------------------------------------------------------
# TIME ANALYSIS
# ------------------------------------------------------------

time_col = None

for c in ["entry_time", "retest_time", "structure_break_time"]:
    if c in df.columns:
        time_col = c
        break

if time_col:

    print("\n" + "=" * 70)
    print("TIME OF DAY ANALYSIS")
    print("=" * 70)

    df["_TIME"] = pd.to_datetime(
        df[time_col],
        errors="coerce"
    )

    df["_HOUR"] = df["_TIME"].dt.hour

    hourly = (
        df.groupby("_HOUR")
        .agg(
            trades=("WIN", "size"),
            wins=("WIN", "sum"),
            losses=("LOSS", "sum")
        )
    )

    hourly["win_rate"] = (
        hourly["wins"] /
        (hourly["wins"] + hourly["losses"]) * 100
    )

    print(hourly.round(2).to_string())

# ------------------------------------------------------------
# COMBINED BUY CONDITIONS
# ------------------------------------------------------------

if direction_col:

    print("\n" + "=" * 70)
    print("BUY / SELL + FEATURE ANALYSIS")
    print("=" * 70)

    df["_SIDE"] = (
        df[direction_col]
        .astype(str)
        .str.upper()
        .apply(
            lambda x:
            "BUY" if "BUY" in x or "BULL" in x
            else "SELL" if "SELL" in x or "BEAR" in x
            else "OTHER"
        )
    )

    for side in ["BUY", "SELL"]:

        x = df[df["_SIDE"] == side].copy()

        if len(x) == 0:
            continue

        print(f"\n--- {side} ---")

        for feature in features:

            if feature not in x.columns:
                continue

            x[feature] = pd.to_numeric(
                x[feature],
                errors="coerce"
            )

            x = x.dropna(subset=[feature])

            if len(x) < 8:
                continue

            median = x[feature].median()

            low = x[x[feature] <= median]
            high = x[x[feature] > median]

            if len(low) >= 3:
                wr = low["WIN"].mean() * 100
                print(
                    f"{feature} <= {median:.2f} "
                    f"| trades={len(low)} "
                    f"| winrate={wr:.2f}%"
                )

            if len(high) >= 3:
                wr = high["WIN"].mean() * 100
                print(
                    f"{feature} >  {median:.2f} "
                    f"| trades={len(high)} "
                    f"| winrate={wr:.2f}%"
                )

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
