import pandas as pd
from pathlib import Path


# ============================================================
# FILES
# ============================================================

INPUT_FILE = Path(
    "data/processed/XAUUSDT-5m-with-signals.csv"
)

OUTPUT_FILE = Path(
    "data/processed/backtest_trades.csv"
)


# ============================================================
# ACCOUNT SETTINGS
# ============================================================

STARTING_BALANCE = 10000.0

RISK_PCT = 0.005          # 0.5%

MAX_QUANTITY = 0.5        # maximum 0.5 lots/units

SL_BUFFER = 1.0           # $1 beyond S/R zone

RR = 2.0                  # V1 = 1:2


# ============================================================
# LOAD DATA
# ============================================================

print("Loading data...")

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["open_time"]
)

df = df.reset_index(drop=True)

print(f"Candles loaded: {len(df)}")


# ============================================================
# ACCOUNT
# ============================================================

balance = STARTING_BALANCE

trades = []

position_open = False

next_available_index = 0


# ============================================================
# SIGNALS
# ============================================================

signal_indices = df.index[
    df["signal"].notna()
].tolist()


# ============================================================
# PROCESS SIGNALS
# ============================================================

for signal_idx in signal_indices:

    # --------------------------------------------------------
    # ONE POSITION AT A TIME
    # --------------------------------------------------------

    if signal_idx < next_available_index:
        continue


    # --------------------------------------------------------
    # Need next candle for entry
    # --------------------------------------------------------

    entry_idx = signal_idx + 1

    if entry_idx >= len(df):
        continue


    signal_row = df.loc[signal_idx]

    entry_row = df.loc[entry_idx]


    signal = signal_row["signal"]

    entry_price = float(
        entry_row["open"]
    )

    entry_time = entry_row["open_time"]


    # --------------------------------------------------------
    # S/R ZONE
    # --------------------------------------------------------

    zone_low = float(
        signal_row["zone_low"]
    )

    zone_high = float(
        signal_row["zone_high"]
    )


    # --------------------------------------------------------
    # STOP LOSS
    # --------------------------------------------------------

    if signal == "BUY":

        stop_loss = (
            zone_low - SL_BUFFER
        )

        stop_distance = (
            entry_price - stop_loss
        )

    else:

        stop_loss = (
            zone_high + SL_BUFFER
        )

        stop_distance = (
            stop_loss - entry_price
        )


    # Invalid trade
    if stop_distance <= 0:
        continue


    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    risk_dollars = (
        balance * RISK_PCT
    )


    # --------------------------------------------------------
    # POSITION SIZE
    # --------------------------------------------------------

    quantity = (
        risk_dollars
        / stop_distance
    )


    # Maximum quantity
    quantity = min(
        quantity,
        MAX_QUANTITY
    )


    # Actual risk after quantity cap
    actual_risk = (
        stop_distance
        * quantity
    )


    # --------------------------------------------------------
    # TAKE PROFIT
    # --------------------------------------------------------

    if signal == "BUY":

        take_profit = (
            entry_price
            + stop_distance * RR
        )

    else:

        take_profit = (
            entry_price
            - stop_distance * RR
        )


    # --------------------------------------------------------
    # SEARCH FOR EXIT
    # --------------------------------------------------------

    exit_price = None

    exit_time = None

    exit_reason = None

    exit_idx = None


    for i in range(
        entry_idx,
        len(df)
    ):

        row = df.loc[i]


        # ----------------------------------------------------
        # BUY
        # ----------------------------------------------------

        if signal == "BUY":

            hit_sl = (
                row["low"]
                <= stop_loss
            )

            hit_tp = (
                row["high"]
                >= take_profit
            )


            # Conservative assumption:
            # if both happen inside one candle,
            # assume SL happened first.

            if hit_sl:

                exit_price = stop_loss

                exit_reason = "SL"

            elif hit_tp:

                exit_price = take_profit

                exit_reason = "TP"


        # ----------------------------------------------------
        # SELL
        # ----------------------------------------------------

        else:

            hit_sl = (
                row["high"]
                >= stop_loss
            )

            hit_tp = (
                row["low"]
                <= take_profit
            )


            if hit_sl:

                exit_price = stop_loss

                exit_reason = "SL"

            elif hit_tp:

                exit_price = take_profit

                exit_reason = "TP"


        # ----------------------------------------------------
        # EXIT FOUND
        # ----------------------------------------------------

        if exit_price is not None:

            exit_time = row["open_time"]

            exit_idx = i

            break


    # --------------------------------------------------------
    # Trade still open at end of dataset
    # --------------------------------------------------------

    if exit_price is None:

        continue


    # ========================================================
    # P&L
    # ========================================================

    if signal == "BUY":

        pnl = (
            exit_price
            - entry_price
        ) * quantity

    else:

        pnl = (
            entry_price
            - exit_price
        ) * quantity


    # ========================================================
    # UPDATE BALANCE
    # ========================================================

    balance += pnl


    # ========================================================
    # SAVE TRADE
    # ========================================================

    trades.append({

        "entry_time":
            entry_time,

        "exit_time":
            exit_time,

        "signal":
            signal,

        "entry_price":
            entry_price,

        "stop_loss":
            stop_loss,

        "take_profit":
            take_profit,

        "exit_price":
            exit_price,

        "exit_reason":
            exit_reason,

        "zone_low":
            zone_low,

        "zone_high":
            zone_high,

        "stop_distance":
            stop_distance,

        "quantity":
            quantity,

        "planned_risk":
            risk_dollars,

        "actual_risk":
            actual_risk,

        "pnl_dollars":
            pnl,

        "balance_after":
            balance,

        "signal_index":
            signal_idx,

        "exit_index":
            exit_idx

    })


    # ========================================================
    # LOCK POSITION
    # ========================================================

    next_available_index = (
        exit_idx + 1
    )


# ============================================================
# RESULTS
# ============================================================

trades_df = pd.DataFrame(
    trades
)


# ============================================================
# SAVE
# ============================================================

trades_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# STATISTICS
# ============================================================

if len(trades_df) > 0:

    winning = (
        trades_df["pnl_dollars"] > 0
    ).sum()

    losing = (
        trades_df["pnl_dollars"] < 0
    ).sum()

    win_rate = (
        winning
        / len(trades_df)
        * 100
    )

    gross_profit = trades_df.loc[
        trades_df["pnl_dollars"] > 0,
        "pnl_dollars"
    ].sum()

    gross_loss = abs(
        trades_df.loc[
            trades_df["pnl_dollars"] < 0,
            "pnl_dollars"
        ].sum()
    )

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0
        else float("inf")
    )

    average_trade = (
        trades_df["pnl_dollars"].mean()
    )

    max_quantity = (
        trades_df["quantity"].max()
    )

else:

    winning = 0
    losing = 0
    win_rate = 0
    profit_factor = 0
    average_trade = 0
    max_quantity = 0


# ============================================================
# PRINT RESULTS
# ============================================================

print()
print("======================================")
print("        V1 REALISTIC BACKTEST")
print("======================================")

print(
    f"Starting balance : ${STARTING_BALANCE:,.2f}"
)

print(
    f"Final balance    : ${balance:,.2f}"
)

print(
    f"Net P/L          : "
    f"${balance - STARTING_BALANCE:,.2f}"
)

print(
    f"Total trades     : {len(trades_df)}"
)

print(
    f"Winning trades   : {winning}"
)

print(
    f"Losing trades    : {losing}"
)

print(
    f"Win rate         : {win_rate:.2f}%"
)

print(
    f"Profit factor    : {profit_factor:.2f}"
)

print(
    f"Average trade    : ${average_trade:.2f}"
)

print(
    f"Maximum quantity : {max_quantity:.4f}"
)

print(
    f"Risk per trade   : {RISK_PCT * 100:.2f}%"
)

print(
    f"RR               : 1:{RR:.1f}"
)

print(
    f"SL buffer        : ${SL_BUFFER:.2f}"
)

print()
print(
    f"Saved trade log to {OUTPUT_FILE}"
)

print("======================================")