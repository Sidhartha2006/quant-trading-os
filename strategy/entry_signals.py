import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = Path("data/processed/XAUUSDT-5m-combined.csv")


OUTPUT_FILE = Path(
    "data/processed/XAUUSDT-5m-with-signals.csv"
)

# Swing detection
SWING_LEFT = 3
SWING_RIGHT = 3

# How close price must be to an HTF level
LEVEL_TOLERANCE = 0.0025       # 0.25%

# M30 liquidity tolerance
LIQUIDITY_TOLERANCE = 0.0015   # 0.15%

# Breakout/retest settings
BREAKOUT_LOOKBACK = 12         # execution candles
RETEST_WINDOW = 8              # candles allowed after breakout

# Minimum RR used only for signal filtering
MIN_RR = 2.0


# ============================================================
# LOAD DATA
# ============================================================

print("Loading XAUUSDT data...")

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["open_time"]
)

df = df.sort_values("open_time").reset_index(drop=True)

print(f"Candles loaded: {len(df):,}")


# ============================================================
# BASIC VALIDATION
# ============================================================

required = [
    "open_time",
    "open",
    "high",
    "low",
    "close"
]

for col in required:
    if col not in df.columns:
        raise ValueError(
            f"Missing required column: {col}"
        )


# ============================================================
# RESAMPLE TIMEFRAMES
# ============================================================

def resample_ohlc(data, timeframe):

    x = data.set_index("open_time")

    result = x.resample(
        timeframe,
        label="right",
        closed="right"
    ).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last"
    })

    result = result.dropna().reset_index()

    return result


print("Building higher timeframes...")

m30 = resample_ohlc(df, "30min")
h4 = resample_ohlc(df, "4h")
d1 = resample_ohlc(df, "1D")

print(f"M30 candles: {len(m30):,}")
print(f"H4 candles : {len(h4):,}")
print(f"D1 candles : {len(d1):,}")


# ============================================================
# CONFIRMED SWINGS
# ============================================================

def find_confirmed_swings(data):

    highs = []
    lows = []

    high_values = data["high"].values
    low_values = data["low"].values

    for i in range(
        SWING_LEFT,
        len(data) - SWING_RIGHT
    ):

        left_high = high_values[
            i - SWING_LEFT:i
        ]

        right_high = high_values[
            i + 1:i + SWING_RIGHT + 1
        ]

        left_low = low_values[
            i - SWING_LEFT:i
        ]

        right_low = low_values[
            i + 1:i + SWING_RIGHT + 1
        ]

        if (
            high_values[i] > left_high.max()
            and
            high_values[i] >= right_high.max()
        ):
            highs.append({
                "time": data.iloc[i]["open_time"],
                "price": high_values[i]
            })

        if (
            low_values[i] < left_low.min()
            and
            low_values[i] <= right_low.min()
        ):
            lows.append({
                "time": data.iloc[i]["open_time"],
                "price": low_values[i]
            })

    return highs, lows


print("Finding higher-timeframe structure...")

m30_highs, m30_lows = find_confirmed_swings(m30)
h4_highs, h4_lows = find_confirmed_swings(h4)
d1_highs, d1_lows = find_confirmed_swings(d1)

print(f"M30 swing highs: {len(m30_highs)}")
print(f"M30 swing lows : {len(m30_lows)}")

print(f"H4 swing highs : {len(h4_highs)}")
print(f"H4 swing lows  : {len(h4_lows)}")

print(f"D1 swing highs : {len(d1_highs)}")
print(f"D1 swing lows  : {len(d1_lows)}")


# ============================================================
# CONVERT SWINGS TO DATAFRAMES
# ============================================================

def swings_to_df(swings):

    if not swings:
        return pd.DataFrame(
            columns=["time", "price"]
        )

    return pd.DataFrame(swings)


m30_high_df = swings_to_df(m30_highs)
m30_low_df = swings_to_df(m30_lows)

h4_high_df = swings_to_df(h4_highs)
h4_low_df = swings_to_df(h4_lows)

d1_high_df = swings_to_df(d1_highs)
d1_low_df = swings_to_df(d1_lows)


# ============================================================
# CAUSAL LEVEL LOOKUP
# ============================================================

def latest_level_before(
    swing_df,
    current_time
):

    if swing_df.empty:
        return np.nan

    valid = swing_df[
        swing_df["time"] < current_time
    ]

    if valid.empty:
        return np.nan

    return float(
        valid.iloc[-1]["price"]
    )


# ============================================================
# LEVEL PROXIMITY
# ============================================================

def near_level(price, level, tolerance):

    if pd.isna(level):
        return False

    return (
        abs(price - level)
        / level
        <= tolerance
    )


# ============================================================
# CANDLE DIRECTION
# ============================================================

def bullish_candle(row):

    return row["close"] > row["open"]


def bearish_candle(row):

    return row["close"] < row["open"]


# ============================================================
# BUILD SIGNALS
# ============================================================

signals = []

print()
print("Generating multi-timeframe signals...")
print()


for i in range(len(df)):

    row = df.iloc[i]

    current_time = row["open_time"]

    close = float(row["close"])
    high = float(row["high"])
    low = float(row["low"])

    # --------------------------------------------------------
    # 1D STRUCTURE
    # --------------------------------------------------------

    daily_resistance = latest_level_before(
        d1_high_df,
        current_time
    )

    daily_support = latest_level_before(
        d1_low_df,
        current_time
    )

    # --------------------------------------------------------
    # H4 STRUCTURE
    # --------------------------------------------------------

    h4_resistance = latest_level_before(
        h4_high_df,
        current_time
    )

    h4_support = latest_level_before(
        h4_low_df,
        current_time
    )

    # --------------------------------------------------------
    # M30 LIQUIDITY
    # --------------------------------------------------------

    m30_resistance = latest_level_before(
        m30_high_df,
        current_time
    )

    m30_support = latest_level_before(
        m30_low_df,
        current_time
    )

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    daily_buy_context = near_level(
        close,
        daily_support,
        LEVEL_TOLERANCE
    )

    daily_sell_context = near_level(
        close,
        daily_resistance,
        LEVEL_TOLERANCE
    )

    h4_sell_context = near_level(
        close,
        h4_resistance,
        LEVEL_TOLERANCE
    )

    h4_buy_context = near_level(
        close,
        h4_support,
        LEVEL_TOLERANCE
    )

    # --------------------------------------------------------
    # WE WANT H4 TO PROVIDE THE IMMEDIATE TRADE AREA
    # --------------------------------------------------------

    sell_setup = (
        h4_sell_context
        or
        (
            not pd.isna(h4_resistance)
            and high >= h4_resistance
        )
    )

    buy_setup = (
        h4_buy_context
        or
        (
            not pd.isna(h4_support)
            and low <= h4_support
        )
    )

    # --------------------------------------------------------
    # LIQUIDITY SWEEP
    # --------------------------------------------------------

    sell_liquidity = False

    if not pd.isna(m30_resistance):

        sell_liquidity = (
            high >= m30_resistance
            and
            close < m30_resistance
        )

    buy_liquidity = False

    if not pd.isna(m30_support):

        buy_liquidity = (
            low <= m30_support
            and
            close > m30_support
        )

    # --------------------------------------------------------
    # BREAKOUT + RETEST
    #
    # Because current dataset is 5m, this is our
    # execution timeframe.
    # --------------------------------------------------------

    if i < BREAKOUT_LOOKBACK + RETEST_WINDOW:

        continue

    previous_high = df.iloc[
        i - BREAKOUT_LOOKBACK:i
    ]["high"].max()

    previous_low = df.iloc[
        i - BREAKOUT_LOOKBACK:i
    ]["low"].min()

    # --------------------------------------------------------
    # BULLISH BREAKOUT
    # --------------------------------------------------------

    bullish_breakout = (
        close > previous_high
    )

    # --------------------------------------------------------
    # BEARISH BREAKOUT
    # --------------------------------------------------------

    bearish_breakout = (
        close < previous_low
    )

    # --------------------------------------------------------
    # RETEST DETECTION
    #
    # Look backwards for a recent breakout.
    # --------------------------------------------------------

    recent = df.iloc[
        max(0, i - RETEST_WINDOW):i
    ]

    bullish_retest = False

    bearish_retest = False

    if len(recent) > 0:

        # Recent bullish breakout
        for j in range(
            len(recent)
        ):

            rr = recent.iloc[j]

            if rr["close"] > previous_high:

                breakout_level = previous_high

                if (
                    low <= breakout_level
                    and
                    close > breakout_level
                    and
                    bullish_candle(row)
                ):
                    bullish_retest = True

                    break

        # Recent bearish breakout
        for j in range(
            len(recent)
        ):

            rr = recent.iloc[j]

            if rr["close"] < previous_low:

                breakout_level = previous_low

                if (
                    high >= breakout_level
                    and
                    close < breakout_level
                    and
                    bearish_candle(row)
                ):
                    bearish_retest = True

                    break

    # ========================================================
    # BUY
    # ========================================================

    if (
        buy_setup
        and
        buy_liquidity
        and
        bullish_breakout
        and
        bullish_retest
    ):

        zone_price = (
            h4_support
            if not pd.isna(h4_support)
            else m30_support
        )

        signals.append({

            "open_time": current_time,

            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],

            "signal": "BUY",

            "daily_support": daily_support,
            "daily_resistance": daily_resistance,

            "h4_support": h4_support,
            "h4_resistance": h4_resistance,

            "m30_support": m30_support,
            "m30_resistance": m30_resistance,

            "zone_price": zone_price,

            "signal_reason":
                "MTF BUY: H4 support + M30 liquidity sweep + breakout + retest",

            "entry_type":
                "Breakout Retest"

        })

    # ========================================================
    # SELL
    # ========================================================

    elif (
        sell_setup
        and
        sell_liquidity
        and
        bearish_breakout
        and
        bearish_retest
    ):

        zone_price = (
            h4_resistance
            if not pd.isna(h4_resistance)
            else m30_resistance
        )

        signals.append({

            "open_time": current_time,

            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],

            "signal": "SELL",

            "daily_support": daily_support,
            "daily_resistance": daily_resistance,

            "h4_support": h4_support,
            "h4_resistance": h4_resistance,

            "m30_support": m30_support,
            "m30_resistance": m30_resistance,

            "zone_price": zone_price,

            "signal_reason":
                "MTF SELL: H4 resistance + M30 liquidity sweep + breakout + retest",

            "entry_type":
                "Breakout Retest"

        })


# ============================================================
# SAVE
# ============================================================

signals_df = pd.DataFrame(signals)


# Make sure output has same chronological ordering
if not signals_df.empty:

    signals_df = signals_df.sort_values(
        "open_time"
    ).reset_index(drop=True)


# ============================================================
# MERGE SIGNALS BACK INTO ORIGINAL DATA
# ============================================================

df["signal"] = np.nan
df["signal_reason"] = np.nan
df["entry_type"] = np.nan

if not signals_df.empty:

    signal_map = signals_df.set_index(
        "open_time"
    )

    for idx in df.index:

        t = df.at[idx, "open_time"]

        if t in signal_map.index:

            df.at[idx, "signal"] = (
                signal_map.loc[t, "signal"]
            )

            df.at[idx, "signal_reason"] = (
                signal_map.loc[t, "signal_reason"]
            )

            df.at[idx, "entry_type"] = (
                signal_map.loc[t, "entry_type"]
            )


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# REPORT
# ============================================================

buy_count = int(
    (df["signal"] == "BUY").sum()
)

sell_count = int(
    (df["signal"] == "SELL").sum()
)

total = buy_count + sell_count


print()
print("======================================")
print("       MTF LIQUIDITY STRATEGY V2")
print("======================================")

print(
    f"Candles       : {len(df):,}"
)

print(
    f"BUY signals   : {buy_count}"
)

print(
    f"SELL signals  : {sell_count}"
)

print(
    f"TOTAL signals : {total}"
)

print()

if total > 0:

    print("First signals:")

    print(
        df[
            df["signal"].notna()
        ][[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "signal",
            "signal_reason"
        ]].head(20).to_string(
            index=False
        )
    )

else:

    print(
        "No signals generated."
    )

print()
print(
    f"Saved to: {OUTPUT_FILE}"
)
print("======================================")