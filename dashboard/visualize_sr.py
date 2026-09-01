import matplotlib
matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from pathlib import Path


# ============================================================
# FILES
# ============================================================

INPUT_FILE = Path(
    "data/processed/XAUUSDT-5m-with-signals.csv"
)

OUTPUT_DIR = Path(
    "data/processed/charts"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SETTINGS
# ============================================================

CANDLES_TO_SHOW = 500

CANDLE_WIDTH_MINUTES = 3.5

BUY_OFFSET = 1.5
SELL_OFFSET = 1.5


# ============================================================
# LOAD DATA
# ============================================================

print("Loading signal data...")

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["open_time"]
)

df = df.reset_index(drop=True)

print(f"Total candles: {len(df)}")


# ============================================================
# FIND SIGNAL WINDOWS
# ============================================================

signal_indices = df.index[
    df["signal"].notna()
].tolist()

print(f"Total signals: {len(signal_indices)}")


if not signal_indices:
    print("No signals found.")
    raise SystemExit


# ============================================================
# CREATE WINDOWS AROUND SIGNALS
# ============================================================

windows = []

half_window = CANDLES_TO_SHOW // 2

for signal_idx in signal_indices:

    start = max(
        0,
        signal_idx - half_window
    )

    end = min(
        len(df),
        signal_idx + half_window
    )

    windows.append(
        (start, end, signal_idx)
    )


# ============================================================
# LIMIT NUMBER OF CHARTS
# ============================================================

# We don't want hundreds of charts immediately.
# Start with the first 10 signals.

windows = windows[:10]


# ============================================================
# DRAW ONE CHART PER SIGNAL
# ============================================================

for chart_number, (
    start,
    end,
    signal_idx
) in enumerate(windows, start=1):

    df_plot = df.iloc[start:end].copy()

    signal_row = df.loc[signal_idx]

    signal_time = signal_row["open_time"]

    signal_type = signal_row["signal"]

    zone_low = signal_row["zone_low"]

    zone_high = signal_row["zone_high"]

    zone_price = signal_row["zone_price"]

    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(18, 9)
    )

    # --------------------------------------------------------
    # Candle width
    # --------------------------------------------------------

    candle_width = (
        CANDLE_WIDTH_MINUTES
        / (24 * 60)
    )

    # --------------------------------------------------------
    # Draw candles
    # --------------------------------------------------------

    for _, row in df_plot.iterrows():

        x = mdates.date2num(
            row["open_time"]
        )

        open_price = row["open"]
        high_price = row["high"]
        low_price = row["low"]
        close_price = row["close"]

        # Wick
        ax.plot(
            [x, x],
            [low_price, high_price],
            linewidth=0.8
        )

        # Body
        bottom = min(
            open_price,
            close_price
        )

        height = abs(
            close_price - open_price
        )

        if height == 0:
            height = 0.01

        if close_price >= open_price:
            face_color = "white"
        else:
            face_color = "black"

        candle = Rectangle(
            (
                x - candle_width / 2,
                bottom
            ),
            candle_width,
            height,
            facecolor=face_color,
            edgecolor="black",
            linewidth=0.7
        )

        ax.add_patch(candle)

    # --------------------------------------------------------
    # Draw S/R zone
    # --------------------------------------------------------

    ax.axhspan(
        zone_low,
        zone_high,
        alpha=0.18,
        label=(
            f"{'Support' if signal_type == 'BUY' else 'Resistance'} "
            f"Zone"
        )
    )

    # Middle zone line
    ax.axhline(
        zone_price,
        linewidth=1.2,
        linestyle="--",
        alpha=0.7
    )

    # --------------------------------------------------------
    # Signal candle
    # --------------------------------------------------------

    signal_x = mdates.date2num(
        signal_row["open_time"]
    )

    if signal_type == "BUY":

        ax.scatter(
            signal_x,
            signal_row["low"] - BUY_OFFSET,
            marker="^",
            s=150,
            label="BUY Signal"
        )

    else:

        ax.scatter(
            signal_x,
            signal_row["high"] + SELL_OFFSET,
            marker="v",
            s=150,
            label="SELL Signal"
        )

    # --------------------------------------------------------
    # Vertical signal marker
    # --------------------------------------------------------

    ax.axvline(
        signal_x,
        linestyle=":",
        linewidth=1,
        alpha=0.5
    )

    # --------------------------------------------------------
    # Signal information
    # --------------------------------------------------------

    touch_number = signal_row[
        "touch_number"
    ]

    title = (
        f"XAUUSDT 5M — "
        f"{signal_type} Signal #{chart_number}\n"
        f"{signal_time} | "
        f"Zone: {zone_low:.2f} - {zone_high:.2f} | "
        f"Touches: {touch_number:.0f}"
    )

    ax.set_title(
        title,
        fontsize=14
    )

    ax.set_xlabel(
        "Time"
    )

    ax.set_ylabel(
        "Price"
    )

    # --------------------------------------------------------
    # X-axis
    # --------------------------------------------------------

    ax.xaxis_date()

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter(
            "%m-%d %H:%M"
        )
    )

    plt.xticks(
        rotation=45
    )

    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    ax.grid(
        alpha=0.2
    )

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------

    ax.legend()

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    plt.tight_layout()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_file = (
        OUTPUT_DIR
        / f"signal_{chart_number:02d}_{signal_type}.png"
    )

    plt.savefig(
        output_file,
        dpi=150
    )

    plt.close()

    print(
        f"Saved: {output_file}"
    )


print()
print("======================================")
print("S/R VISUALIZATION COMPLETE")
print("======================================")
print(f"Charts created: {len(windows)}")
print(f"Location: {OUTPUT_DIR}")
