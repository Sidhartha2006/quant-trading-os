import matplotlib
matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path


# ============================================================
# FILES
# ============================================================

INPUT_FILE = Path(
    "data/processed/XAUUSDT-5m-with-signals.csv"
)

OUTPUT_FILE = Path(
    "data/processed/xauusdt_signals_chart.png"
)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["open_time"]
)

df = df.reset_index(drop=True)


# ============================================================
# SELECT A SMALL WINDOW
# ============================================================

# First 500 candles for easy visual inspection.
df_plot = df.iloc[:500].copy()


# ============================================================
# CREATE FIGURE
# ============================================================

fig, ax = plt.subplots(
    figsize=(18, 9)
)


# ============================================================
# CANDLE WIDTH
# ============================================================

# 5-minute candles.
# Matplotlib date units are measured in DAYS.
candle_width = 4 / (24 * 60)


# ============================================================
# DRAW CANDLES
# ============================================================

for i, row in df_plot.iterrows():

    # IMPORTANT:
    # Convert Timestamp -> Matplotlib numeric date.
    x = mdates.date2num(row["open_time"])

    open_price = float(row["open"])
    high_price = float(row["high"])
    low_price = float(row["low"])
    close_price = float(row["close"])


    # --------------------------------------------------------
    # Wick
    # --------------------------------------------------------

    ax.plot(
        [x, x],
        [low_price, high_price],
        linewidth=1
    )


    # --------------------------------------------------------
    # Candle body
    # --------------------------------------------------------

    bottom = min(
        open_price,
        close_price
    )

    height = abs(
        close_price - open_price
    )


    # Avoid invisible candle body
    if height == 0:
        height = 0.01


    # Bullish / bearish candle
    if close_price >= open_price:
        face_color = "white"
    else:
        face_color = "black"


    rectangle = plt.Rectangle(
        (
            x - candle_width / 2,
            bottom
        ),
        candle_width,
        height,
        facecolor=face_color,
        edgecolor="black",
        linewidth=0.8
    )

    ax.add_patch(rectangle)


# ============================================================
# SIGNALS
# ============================================================

buy = df_plot[
    df_plot["signal"] == "BUY"
]

sell = df_plot[
    df_plot["signal"] == "SELL"
]


# ============================================================
# BUY MARKERS
# ============================================================

if not buy.empty:

    buy_x = mdates.date2num(
        buy["open_time"]
    )

    ax.scatter(
        buy_x,
        buy["low"] - 1.5,
        marker="^",
        s=70,
        label="BUY"
    )


# ============================================================
# SELL MARKERS
# ============================================================

if not sell.empty:

    sell_x = mdates.date2num(
        sell["open_time"]
    )

    ax.scatter(
        sell_x,
        sell["high"] + 1.5,
        marker="v",
        s=70,
        label="SELL"
    )


# ============================================================
# TRENDLINES AT SIGNALS
# ============================================================

# Only draw trendlines if these columns actually exist.
# This makes the visualization robust.

if (
    "trendline_slope" in df_plot.columns
    and
    "trendline_intercept" in df_plot.columns
):

    signal_df = df_plot[
        df_plot["signal"].notna()
    ].copy()


    for _, row in signal_df.iterrows():

        if pd.isna(
            row["trendline_slope"]
        ):
            continue

        if pd.isna(
            row["trendline_intercept"]
        ):
            continue


        slope = float(
            row["trendline_slope"]
        )

        intercept = float(
            row["trendline_intercept"]
        )


        # ----------------------------------------------------
        # Draw short trendline around signal
        # ----------------------------------------------------

        x_start = max(
            0,
            int(row.name) - 80
        )

        x_end = min(
            len(df_plot) - 1,
            int(row.name) + 10
        )


        x_indices = list(
            range(
                x_start,
                x_end + 1
            )
        )


        y_values = [
            slope * x + intercept
            for x in x_indices
        ]


        x_dates = mdates.date2num(
            df_plot.loc[
                x_indices,
                "open_time"
            ]
        )


        ax.plot(
            x_dates,
            y_values,
            linewidth=1,
            alpha=0.35
        )


# ============================================================
# FORMAT CHART
# ============================================================

ax.set_title(
    "XAUUSDT 5-Minute Strategy Signals"
)

ax.set_xlabel(
    "Time"
)

ax.set_ylabel(
    "Price"
)


# ============================================================
# TIME AXIS
# ============================================================

ax.xaxis_date()

ax.xaxis.set_major_formatter(
    mdates.DateFormatter(
        "%m-%d %H:%M"
    )
)

plt.xticks(
    rotation=45
)


# ============================================================
# GRID
# ============================================================

ax.grid(
    alpha=0.2
)


# ============================================================
# LEGEND
# ============================================================

ax.legend()


# ============================================================
# SAVE
# ============================================================

plt.tight_layout()

plt.savefig(
    OUTPUT_FILE,
    dpi=150,
    bbox_inches="tight"
)

plt.close()


print(
    f"Chart saved to: {OUTPUT_FILE}"
)