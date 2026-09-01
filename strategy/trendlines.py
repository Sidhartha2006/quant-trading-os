import pandas as pd
from pathlib import Path
from support_resistance import find_swing_highs, find_swing_lows

INPUT_FILE = Path("data/processed/XAUUSDT-5m-combined.csv")
TOLERANCE_PCT = 0.001   # how close a point needs to be to the line to "count"
MIN_POINTS = 3           # need at least 3 swing points touching the same trendline

df = pd.read_csv(INPUT_FILE, parse_dates=["open_time"])
df["swing_high"] = find_swing_highs(df)
df["swing_low"] = find_swing_lows(df)
df["idx"] = range(len(df))  # simple numeric x-axis instead of timestamps, for line math

def line_value_at(x1, y1, x2, y2, x):
    """Given two points (x1,y1) and (x2,y2), find the line's y-value at position x."""
    slope = (y2 - y1) / (x2 - x1)
    return y1 + slope * (x - x1)

def find_trendlines(points_df, price_col, tolerance_pct, min_points, direction):
    """
    points_df: dataframe of swing points, must have 'idx' and price_col
    direction: 'resistance' (line above price, swing highs) or 'support' (line below price, swing lows)
    """
    points = points_df.reset_index(drop=True)
    trendlines = []

    n = len(points)
    for i in range(n):
        for j in range(i + 1, n):
            x1, y1 = points.loc[i, "idx"], points.loc[i, price_col]
            x2, y2 = points.loc[j, "idx"], points.loc[j, price_col]

            if x2 == x1:
                continue

            # A resistance trendline should slope so later highs are lower or equal (or forming a clear angle)
            # A support trendline should slope so later lows are higher or equal
            touching = [i, j]

            for k in range(n):
                if k in (i, j):
                    continue
                xk, yk = points.loc[k, "idx"], points.loc[k, price_col]
                line_y = line_value_at(x1, y1, x2, y2, xk)

                if abs(yk - line_y) / line_y <= tolerance_pct:
                    # For resistance: price should stay AT or BELOW the line (not break above it)
                    # For support: price should stay AT or ABOVE the line (not break below it)
                    if direction == "resistance" and yk <= line_y * (1 + tolerance_pct):
                        touching.append(k)
                    elif direction == "support" and yk >= line_y * (1 - tolerance_pct):
                        touching.append(k)

            if len(touching) >= min_points:
                trendlines.append({
                    "point_indices": sorted(set(touching)),
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "num_touches": len(set(touching)),
                })

    return trendlines

resistance_points = df[df["swing_high"]][["idx", "high", "open_time"]].rename(columns={"high": "price"})
support_points = df[df["swing_low"]][["idx", "low", "open_time"]].rename(columns={"low": "price"})

resistance_trendlines = find_trendlines(resistance_points, "price", TOLERANCE_PCT, MIN_POINTS, "resistance")
support_trendlines = find_trendlines(support_points, "price", TOLERANCE_PCT, MIN_POINTS, "support")

print(f"Resistance trendlines found: {len(resistance_trendlines)}")
print(f"Support trendlines found: {len(support_trendlines)}")

if resistance_trendlines:
    print("\nExample resistance trendline:", resistance_trendlines[0])
if support_trendlines:
    print("\nExample support trendline:", support_trendlines[0])