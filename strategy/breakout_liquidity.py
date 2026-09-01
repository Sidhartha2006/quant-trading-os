import pandas as pd
from pathlib import Path


# ============================================================
# FILES
# ============================================================

M30_FILE = Path(
    "data/processed/XAUUSDT-M30-liquidity.csv"
)

OUTPUT_FILE = Path(
    "data/processed/XAUUSDT-M30-breakout-liquidity.csv"
)


# ============================================================
# CONFIG
# ============================================================

BREAKOUT_BUFFER = 1.0

# After a breakout, we don't want to keep the level
# active forever.
MAX_RETEST_CANDLES = 48       # 24 hours on M30


# ============================================================
# LOAD M30 LIQUIDITY
# ============================================================

print("Loading M30 liquidity data...")

levels = pd.read_csv(
    M30_FILE,
    parse_dates=[
        "first_time",
        "last_time"
    ]
)

print(
    f"Liquidity levels loaded: {len(levels)}"
)


# ============================================================
# LOAD ORIGINAL M30 CANDLES
# ============================================================

# We rebuild M30 from the 1M data so that we have
# the actual OHLC candles available for breakout detection.

ONE_MIN_FILE = Path(
    "data/processed/XAUUSDT-1m-combined.csv"
)

print("Loading 1-minute data...")

one_min = pd.read_csv(
    ONE_MIN_FILE,
    parse_dates=["open_time"]
)

one_min = (
    one_min
    .sort_values("open_time")
    .reset_index(drop=True)
)


# ============================================================
# BUILD M30
# ============================================================

print("Building M30 candles...")

m30 = (
    one_min
    .set_index("open_time")
    .resample("30min")
    .agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    })
    .dropna()
    .reset_index()
)

print(
    f"M30 candles: {len(m30):,}"
)


# ============================================================
# FIND BREAKOUTS
# ============================================================

breakouts = []


print("Detecting breakout liquidity...")


for level_idx, level in levels.iterrows():

    level_price = float(
        level["price"]
    )

    level_type = level["type"]

    last_time = level["last_time"]

    # --------------------------------------------------------
    # Only candles AFTER the liquidity level was established
    # --------------------------------------------------------

    future_candles = m30[
        m30["open_time"] > last_time
    ].copy()

    if future_candles.empty:
        continue

    future_candles = future_candles.iloc[
        :MAX_RETEST_CANDLES
    ]

    # --------------------------------------------------------
    # HIGH LIQUIDITY
    #
    # Price breaks ABOVE the high and closes above it.
    # --------------------------------------------------------

    if level_type == "HIGH_LIQUIDITY":

        for _, candle in future_candles.iterrows():

            breakout_price = (
                level_price
                + BREAKOUT_BUFFER
            )

            if (
                candle["close"]
                > breakout_price
            ):

                breakouts.append({

                    "liquidity_price":
                        level_price,

                    "liquidity_type":
                        level_type,

                    "liquidity_touches":
                        int(level["touches"]),

                    "breakout_time":
                        candle["open_time"],

                    "breakout_open":
                        candle["open"],

                    "breakout_high":
                        candle["high"],

                    "breakout_low":
                        candle["low"],

                    "breakout_close":
                        candle["close"],

                    "direction":
                        "BULLISH_BREAKOUT",

                    "retest_low":
                        level_price - BREAKOUT_BUFFER,

                    "retest_high":
                        level_price + BREAKOUT_BUFFER
                })

                # First valid breakout only
                break

    # --------------------------------------------------------
    # LOW LIQUIDITY
    #
    # Price breaks BELOW the low and closes below it.
    # --------------------------------------------------------

    elif level_type == "LOW_LIQUIDITY":

        for _, candle in future_candles.iterrows():

            breakout_price = (
                level_price
                - BREAKOUT_BUFFER
            )

            if (
                candle["close"]
                < breakout_price
            ):

                breakouts.append({

                    "liquidity_price":
                        level_price,

                    "liquidity_type":
                        level_type,

                    "liquidity_touches":
                        int(level["touches"]),

                    "breakout_time":
                        candle["open_time"],

                    "breakout_open":
                        candle["open"],

                    "breakout_high":
                        candle["high"],

                    "breakout_low":
                        candle["low"],

                    "breakout_close":
                        candle["close"],

                    "direction":
                        "BEARISH_BREAKOUT",

                    "retest_low":
                        level_price - BREAKOUT_BUFFER,

                    "retest_high":
                        level_price + BREAKOUT_BUFFER
                })

                break


# ============================================================
# DATAFRAME
# ============================================================

breakout_df = pd.DataFrame(
    breakouts
)


# ============================================================
# REMOVE DUPLICATE BREAKOUTS
# ============================================================

if not breakout_df.empty:

    breakout_df = (
        breakout_df
        .sort_values("breakout_time")
        .drop_duplicates(
            subset=[
                "liquidity_price",
                "breakout_time"
            ]
        )
        .reset_index(drop=True)
    )


# ============================================================
# SAVE
# ============================================================

breakout_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# RESULTS
# ============================================================

print()
print("======================================")
print("      M30 BREAKOUT LIQUIDITY")
print("======================================")

print(
    f"Liquidity levels : {len(levels)}"
)

print(
    f"Breakouts found  : {len(breakout_df)}"
)

if not breakout_df.empty:

    bullish = (
        breakout_df["direction"]
        == "BULLISH_BREAKOUT"
    ).sum()

    bearish = (
        breakout_df["direction"]
        == "BEARISH_BREAKOUT"
    ).sum()

    print(
        f"Bullish breakouts: {bullish}"
    )

    print(
        f"Bearish breakouts: {bearish}"
    )

    print()
    print("First 20 breakouts:")
    print()

    print(
        breakout_df[
            [
                "breakout_time",
                "liquidity_price",
                "liquidity_touches",
                "direction",
                "breakout_close"
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

print()
print(
    f"Saved to: {OUTPUT_FILE}"
)

print("======================================")