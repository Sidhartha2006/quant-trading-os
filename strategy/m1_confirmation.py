import pandas as pd
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

M1_FILE = Path("data/processed/XAUUSDT-1m-combined.csv")
M30_BREAKOUT_FILE = Path(
    "data/processed/XAUUSDT-M30-breakout-liquidity.csv"
)

OUTPUT_FILE = Path(
    "data/processed/XAUUSDT-M1-confirmations.csv"
)

SWING_LOOKBACK = 3

# Maximum distance from broken level for a valid retest
RETEST_TOLERANCE = 1.50

# Maximum number of M1 candles allowed between
# breakout and retest
MAX_RETEST_CANDLES = 30


# ============================================================
# LOAD DATA
# ============================================================

print("======================================")
print("       M1 CONFIRMATION DETECTOR")
print("======================================")

print("Loading 1-minute data...")

m1 = pd.read_csv(
    M1_FILE,
    parse_dates=["open_time"]
)

m1 = m1.reset_index(drop=True)

print(f"M1 candles: {len(m1):,}")


print("\nLoading M30 breakout data...")

breakouts = pd.read_csv(
    M30_BREAKOUT_FILE,
    parse_dates=["breakout_time"]
)

breakouts = breakouts.reset_index(drop=True)

print(f"M30 breakouts: {len(breakouts)}")


# ============================================================
# M1 SWINGS
# ============================================================

print("\nFinding M1 swing points...")

m1["swing_high"] = False
m1["swing_low"] = False

for i in range(
    SWING_LOOKBACK,
    len(m1) - SWING_LOOKBACK
):

    high_window = m1.loc[
        i - SWING_LOOKBACK:
        i + SWING_LOOKBACK,
        "high"
    ]

    low_window = m1.loc[
        i - SWING_LOOKBACK:
        i + SWING_LOOKBACK,
        "low"
    ]

    if m1.at[i, "high"] == high_window.max():
        m1.at[i, "swing_high"] = True

    if m1.at[i, "low"] == low_window.min():
        m1.at[i, "swing_low"] = True


print(
    "M1 swing highs:",
    int(m1["swing_high"].sum())
)

print(
    "M1 swing lows :",
    int(m1["swing_low"].sum())
)


# ============================================================
# STRUCTURE BREAK DETECTION
# ============================================================

def find_recent_swing_high(df, index):

    swings = df.loc[
        :index - 1
    ]

    swings = swings[
        swings["swing_high"]
    ]

    if swings.empty:
        return None

    return swings.iloc[-1]


def find_recent_swing_low(df, index):

    swings = df.loc[
        :index - 1
    ]

    swings = swings[
        swings["swing_low"]
    ]

    if swings.empty:
        return None

    return swings.iloc[-1]


# ============================================================
# PROCESS EACH M30 BREAKOUT
# ============================================================

confirmations = []

print("\nSearching for M1 structure confirmation...")


for _, breakout in breakouts.iterrows():

    breakout_time = breakout["breakout_time"]

    direction = breakout["direction"]

    liquidity_price = float(
        breakout["liquidity_price"]
    )

    # --------------------------------------------------------
    # Find first M1 candle AFTER M30 breakout
    # --------------------------------------------------------

    future = m1[
        m1["open_time"] > breakout_time
    ]

    if future.empty:
        continue

    first_index = future.index[0]

    # --------------------------------------------------------
    # Look for M1 structure break
    # --------------------------------------------------------

    structure_break = None

    search_end = min(
        first_index + MAX_RETEST_CANDLES,
        len(m1)
    )

    for i in range(
        first_index,
        search_end
    ):

        row = m1.loc[i]

        # ====================================================
        # BULLISH BREAKOUT
        # ====================================================

        if direction == "BULLISH_BREAKOUT":

            swing = find_recent_swing_high(
                m1,
                i
            )

            if swing is None:
                continue

            swing_price = float(
                swing["high"]
            )

            # Candle CLOSES above previous M1 swing high
            if row["close"] > swing_price:

                structure_break = {
                    "index": i,
                    "time": row["open_time"],
                    "level": swing_price
                }

                break

        # ====================================================
        # BEARISH BREAKOUT
        # ====================================================

        elif direction == "BEARISH_BREAKOUT":

            swing = find_recent_swing_low(
                m1,
                i
            )

            if swing is None:
                continue

            swing_price = float(
                swing["low"]
            )

            # Candle CLOSES below previous M1 swing low
            if row["close"] < swing_price:

                structure_break = {
                    "index": i,
                    "time": row["open_time"],
                    "level": swing_price
                }

                break

    # --------------------------------------------------------
    # No structure break
    # --------------------------------------------------------

    if structure_break is None:
        continue


    # ========================================================
    # WAIT FOR RETEST
    # ========================================================

    break_index = structure_break["index"]

    broken_level = structure_break["level"]

    retest = None

    retest_end = min(
        break_index + MAX_RETEST_CANDLES,
        len(m1)
    )

    for j in range(
        break_index + 1,
        retest_end
    ):

        row = m1.loc[j]

        # ====================================================
        # BULLISH RETEST
        # ====================================================

        if direction == "BULLISH_BREAKOUT":

            touched = (
                row["low"]
                <= broken_level + RETEST_TOLERANCE
            )

            closed_back_above = (
                row["close"]
                > broken_level
            )

            if touched and closed_back_above:

                retest = {
                    "index": j,
                    "time": row["open_time"],
                    "entry": row["close"]
                }

                break

        # ====================================================
        # BEARISH RETEST
        # ====================================================

        elif direction == "BEARISH_BREAKOUT":

            touched = (
                row["high"]
                >= broken_level - RETEST_TOLERANCE
            )

            closed_back_below = (
                row["close"]
                < broken_level
            )

            if touched and closed_back_below:

                retest = {
                    "index": j,
                    "time": row["open_time"],
                    "entry": row["close"]
                }

                break


    # --------------------------------------------------------
    # No retest
    # --------------------------------------------------------

    if retest is None:
        continue


    # ========================================================
    # CONFIRMED ENTRY
    # ========================================================

    if direction == "BULLISH_BREAKOUT":

        signal = "BUY"

    else:

        signal = "SELL"


    confirmations.append({

        "breakout_time":
            breakout_time,

        "liquidity_price":
            liquidity_price,

        "direction":
            direction,

        "structure_break_time":
            structure_break["time"],

        "structure_level":
            broken_level,

        "retest_time":
            retest["time"],

        "entry_price":
            retest["entry"],

        "signal":
            signal,

        "confirmation":
            "M30 breakout + M1 BOS + M1 retest"

    })


# ============================================================
# SAVE
# ============================================================

result = pd.DataFrame(
    confirmations
)

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# RESULTS
# ============================================================

print("\n======================================")
print("       M1 CONFIRMATION RESULTS")
print("======================================")

print(
    f"M30 breakouts        : {len(breakouts)}"
)

print(
    f"M1 confirmations     : {len(result)}"
)

if not result.empty:

    print(
        "BUY confirmations   :",
        (result["signal"] == "BUY").sum()
    )

    print(
        "SELL confirmations  :",
        (result["signal"] == "SELL").sum()
    )

    print("\nFirst 20 confirmations:")

    print(
        result.head(20).to_string(
            index=False
        )
    )

else:

    print(
        "\nNo M1 confirmations found."
    )


print(
    f"\nSaved to: {OUTPUT_FILE}"
)

print("======================================")