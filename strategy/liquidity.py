import pandas as pd
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = Path(
    "data/processed/XAUUSDT-1m-combined.csv"
)

OUTPUT_FILE = Path(
    "data/processed/XAUUSDT-M30-liquidity.csv"
)

SWING_LOOKBACK = 3

# Maximum distance for grouping nearby liquidity levels
LIQUIDITY_TOLERANCE = 3.0

# Minimum touches for a significant liquidity level
MIN_TOUCHES = 2


# ============================================================
# LOAD 1-MINUTE DATA
# ============================================================

print("Loading 1-minute XAUUSDT data...")

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["open_time"]
)

df = df.sort_values("open_time").reset_index(drop=True)

print(f"1M candles: {len(df):,}")


# ============================================================
# BUILD M30
# ============================================================

print("Building M30 candles...")


m30 = (
    df.set_index("open_time")
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


print(f"M30 candles: {len(m30):,}")


# ============================================================
# FIND SWING HIGHS
# ============================================================

def find_swing_highs(data, lookback=3):

    highs = data["high"]

    result = pd.Series(
        False,
        index=data.index
    )

    for i in range(
        lookback,
        len(data) - lookback
    ):

        current = highs.iloc[i]

        left = highs.iloc[
            i - lookback:i
        ]

        right = highs.iloc[
            i + 1:i + lookback + 1
        ]

        if (
            current >= left.max()
            and current >= right.max()
        ):
            result.iloc[i] = True

    return result


# ============================================================
# FIND SWING LOWS
# ============================================================

def find_swing_lows(data, lookback=3):

    lows = data["low"]

    result = pd.Series(
        False,
        index=data.index
    )

    for i in range(
        lookback,
        len(data) - lookback
    ):

        current = lows.iloc[i]

        left = lows.iloc[
            i - lookback:i
        ]

        right = lows.iloc[
            i + 1:i + lookback + 1
        ]

        if (
            current <= left.min()
            and current <= right.min()
        ):
            result.iloc[i] = True

    return result


# ============================================================
# DETECT SWINGS
# ============================================================

print("Finding M30 swing points...")

m30["swing_high"] = find_swing_highs(
    m30,
    SWING_LOOKBACK
)

m30["swing_low"] = find_swing_lows(
    m30,
    SWING_LOOKBACK
)

print(
    f"M30 swing highs: "
    f"{m30['swing_high'].sum()}"
)

print(
    f"M30 swing lows : "
    f"{m30['swing_low'].sum()}"
)


# ============================================================
# BUILD LIQUIDITY LEVELS
# ============================================================

def build_levels(
    data,
    swing_column,
    price_column,
    liquidity_type
):

    points = data[
        data[swing_column]
    ][
        ["open_time", price_column]
    ].copy()

    levels = []

    for _, point in points.iterrows():

        price = float(
            point[price_column]
        )

        matched = None

        # Find nearby existing level
        for level in levels:

            if abs(
                level["price"] - price
            ) <= LIQUIDITY_TOLERANCE:

                matched = level
                break

        # New level
        if matched is None:

            levels.append({
                "price": price,
                "touches": 1,
                "first_time": point["open_time"],
                "last_time": point["open_time"],
                "type": liquidity_type
            })

        # Existing level
        else:

            old_count = matched["touches"]

            matched["price"] = (
                (
                    matched["price"]
                    * old_count
                )
                + price
            ) / (
                old_count + 1
            )

            matched["touches"] += 1

            matched["last_time"] = (
                point["open_time"]
            )

    return levels


# ============================================================
# HIGH LIQUIDITY
# ============================================================

print("Building high liquidity...")

high_levels = build_levels(
    m30,
    "swing_high",
    "high",
    "HIGH_LIQUIDITY"
)


# ============================================================
# LOW LIQUIDITY
# ============================================================

print("Building low liquidity...")

low_levels = build_levels(
    m30,
    "swing_low",
    "low",
    "LOW_LIQUIDITY"
)


# ============================================================
# COMBINE
# ============================================================

levels = high_levels + low_levels

liquidity = pd.DataFrame(levels)


# ============================================================
# KEEP SIGNIFICANT LEVELS
# ============================================================

liquidity = liquidity[
    liquidity["touches"] >= MIN_TOUCHES
].copy()


# ============================================================
# ZONES
# ============================================================

liquidity["zone_low"] = (
    liquidity["price"]
    - LIQUIDITY_TOLERANCE
)

liquidity["zone_high"] = (
    liquidity["price"]
    + LIQUIDITY_TOLERANCE
)


# ============================================================
# SORT
# ============================================================

liquidity = liquidity.sort_values(
    ["price", "type"]
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

liquidity.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# OUTPUT
# ============================================================

print()
print("======================================")
print("       M30 LIQUIDITY DETECTION")
print("======================================")

print(
    f"M30 candles          : {len(m30):,}"
)

print(
    f"Swing highs          : "
    f"{m30['swing_high'].sum()}"
)

print(
    f"Swing lows           : "
    f"{m30['swing_low'].sum()}"
)

print(
    f"High liquidity       : "
    f"{len(high_levels)}"
)

print(
    f"Low liquidity        : "
    f"{len(low_levels)}"
)

print(
    f"Significant levels   : "
    f"{len(liquidity)}"
)

print()
print("Top liquidity levels:")
print()

print(
    liquidity[
        [
            "price",
            "zone_low",
            "zone_high",
            "touches",
            "type"
        ]
    ]
    .sort_values(
        "touches",
        ascending=False
    )
    .head(20)
    .to_string(index=False)
)

print()
print(
    f"Saved to: {OUTPUT_FILE}"
)

print("======================================")