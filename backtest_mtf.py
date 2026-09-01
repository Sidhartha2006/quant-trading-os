import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

CONFIRMATION_FILE = Path(
    "data/processed/XAUUSDT-M1-valid-confirmations.csv"
)

M1_FILE = Path(
    "data/processed/XAUUSDT-1m-combined.csv"
)

OUTPUT_FILE = Path(
    "data/processed/mtf_backtest_trades.csv"
)


STARTING_BALANCE = 10_000.00

RISK_PER_TRADE = 0.005       # 0.50%
RR = 2.0                     # 1:2

MAX_QUANTITY = 0.50

# Minimum / maximum SL distance
MIN_SL_DISTANCE = 1.0
MAX_SL_DISTANCE = 15.0

# Maximum time to keep a trade open
MAX_HOLDING_MINUTES = 24 * 60


# ============================================================
# LOAD CONFIRMATIONS
# ============================================================

print()
print("=" * 60)
print("       MTF LIQUIDITY + BOS + RETEST BACKTEST")
print("=" * 60)

print()
print("Loading valid confirmations...")

signals = pd.read_csv(
    CONFIRMATION_FILE,
    parse_dates=[
        "breakout_time",
        "structure_break_time",
        "retest_time"
    ]
)

print(
    f"Valid confirmations loaded: {len(signals)}"
)


# ============================================================
# LOAD 1-MINUTE DATA
# ============================================================

print()
print("Loading 1-minute market data...")

m1 = pd.read_csv(
    M1_FILE,
    parse_dates=["open_time"]
)

m1 = m1.sort_values("open_time").reset_index(drop=True)

print(
    f"1-minute candles loaded: {len(m1):,}"
)


# ============================================================
# CLEAN NUMERIC DATA
# ============================================================

numeric_columns = [
    "open",
    "high",
    "low",
    "close"
]

for column in numeric_columns:
    m1[column] = pd.to_numeric(
        m1[column],
        errors="coerce"
    )

signals["entry_price"] = pd.to_numeric(
    signals["entry_price"],
    errors="coerce"
)

signals["liquidity_price"] = pd.to_numeric(
    signals["liquidity_price"],
    errors="coerce"
)

signals["structure_level"] = pd.to_numeric(
    signals["structure_level"],
    errors="coerce"
)


m1 = m1.dropna(
    subset=[
        "open_time",
        "open",
        "high",
        "low",
        "close"
    ]
)

signals = signals.dropna(
    subset=[
        "retest_time",
        "entry_price",
        "structure_level"
    ]
)


# ============================================================
# KEEP ONLY VALID SIGNALS
# ============================================================

signals = signals[
    signals["validation"].astype(str).str.upper() == "VALID"
].copy()

signals = signals.sort_values(
    "retest_time"
).reset_index(drop=True)


print(
    f"VALID signals used: {len(signals)}"
)


# ============================================================
# HELPER: GET FUTURE CANDLES
# ============================================================

def get_future_candles(
    data,
    entry_time,
    max_minutes
):

    end_time = (
        entry_time
        + pd.Timedelta(
            minutes=max_minutes
        )
    )

    future = data[
        (data["open_time"] >= entry_time)
        &
        (data["open_time"] <= end_time)
    ]

    return future


# ============================================================
# DETERMINE SL
# ============================================================

def calculate_stop_loss(
    signal,
    entry
):

    direction = str(
        signal["signal"]
    ).upper()

    structure = float(
        signal["structure_level"]
    )

    liquidity = float(
        signal["liquidity_price"]
    )

    # --------------------------------------------------------
    # BUY
    # --------------------------------------------------------

    if direction == "BUY":

        # For a BUY, SL should be below the
        # structural/retest area.

        reference = min(
            structure,
            liquidity
        )

        sl = reference - 1.0

        distance = entry - sl

        if distance < MIN_SL_DISTANCE:

            sl = entry - MIN_SL_DISTANCE

        if entry - sl > MAX_SL_DISTANCE:

            return None

        return sl

    # --------------------------------------------------------
    # SELL
    # --------------------------------------------------------

    if direction == "SELL":

        # For a SELL, SL should be above the
        # structural/retest area.

        reference = max(
            structure,
            liquidity
        )

        sl = reference + 1.0

        distance = sl - entry

        if distance < MIN_SL_DISTANCE:

            sl = entry + MIN_SL_DISTANCE

        if sl - entry > MAX_SL_DISTANCE:

            return None

        return sl

    return None


# ============================================================
# BACKTEST
# ============================================================

balance = STARTING_BALANCE

trades = []

used_until = None


print()
print("Running backtest...")
print()


for index, signal in signals.iterrows():

    direction = str(
        signal["signal"]
    ).upper()

    entry_time = pd.Timestamp(
        signal["retest_time"]
    )

    entry = float(
        signal["entry_price"]
    )

    # --------------------------------------------------------
    # Prevent overlapping trades
    # --------------------------------------------------------

    if used_until is not None:

        if entry_time <= used_until:
            continue

    # --------------------------------------------------------
    # STOP LOSS
    # --------------------------------------------------------

    sl = calculate_stop_loss(
        signal,
        entry
    )

    if sl is None:
        continue

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    risk_amount = (
        balance
        * RISK_PER_TRADE
    )

    if direction == "BUY":

        risk_per_unit = (
            entry - sl
        )

    elif direction == "SELL":

        risk_per_unit = (
            sl - entry
        )

    else:
        continue

    if risk_per_unit <= 0:
        continue

    quantity = (
        risk_amount
        / risk_per_unit
    )

    quantity = min(
        quantity,
        MAX_QUANTITY
    )

    # --------------------------------------------------------
    # ACTUAL RISK AFTER MAX QUANTITY
    # --------------------------------------------------------

    actual_risk = (
        risk_per_unit
        * quantity
    )

    # --------------------------------------------------------
    # TAKE PROFIT
    # --------------------------------------------------------

    if direction == "BUY":

        tp = (
            entry
            + risk_per_unit * RR
        )

    else:

        tp = (
            entry
            - risk_per_unit * RR
        )

    # --------------------------------------------------------
    # FUTURE MARKET DATA
    # --------------------------------------------------------

    future = get_future_candles(
        m1,
        entry_time,
        MAX_HOLDING_MINUTES
    )

    if future.empty:
        continue

    # --------------------------------------------------------
    # FIND EXIT
    # --------------------------------------------------------

    exit_time = None
    exit_price = None
    exit_reason = None

    for _, candle in future.iterrows():

        candle_high = float(
            candle["high"]
        )

        candle_low = float(
            candle["low"]
        )

        candle_close = float(
            candle["close"]
        )

        candle_time = pd.Timestamp(
            candle["open_time"]
        )

        # ====================================================
        # BUY
        # ====================================================

        if direction == "BUY":

            hit_sl = (
                candle_low <= sl
            )

            hit_tp = (
                candle_high >= tp
            )

            # If both are touched during
            # the same 1-minute candle,
            # use conservative assumption:
            # SL happens first.

            if hit_sl and hit_tp:

                exit_price = sl
                exit_reason = "SL_AND_TP_SAME_CANDLE"

                exit_time = candle_time

                break

            if hit_sl:

                exit_price = sl
                exit_reason = "STOP_LOSS"

                exit_time = candle_time

                break

            if hit_tp:

                exit_price = tp
                exit_reason = "TAKE_PROFIT"

                exit_time = candle_time

                break

        # ====================================================
        # SELL
        # ====================================================

        elif direction == "SELL":

            hit_sl = (
                candle_high >= sl
            )

            hit_tp = (
                candle_low <= tp
            )

            # Conservative assumption if
            # both occur in same candle.

            if hit_sl and hit_tp:

                exit_price = sl
                exit_reason = "SL_AND_TP_SAME_CANDLE"

                exit_time = candle_time

                break

            if hit_sl:

                exit_price = sl
                exit_reason = "STOP_LOSS"

                exit_time = candle_time

                break

            if hit_tp:

                exit_price = tp
                exit_reason = "TAKE_PROFIT"

                exit_time = candle_time

                break

    # --------------------------------------------------------
    # FORCE EXIT
    # --------------------------------------------------------

    if exit_time is None:

        last_candle = future.iloc[-1]

        exit_time = pd.Timestamp(
            last_candle["open_time"]
        )

        exit_price = float(
            last_candle["close"]
        )

        exit_reason = "TIME_EXIT"

    # --------------------------------------------------------
    # CALCULATE P/L
    # --------------------------------------------------------

    if direction == "BUY":

        pnl_per_unit = (
            exit_price - entry
        )

    else:

        pnl_per_unit = (
            entry - exit_price
        )

    pnl = (
        pnl_per_unit
        * quantity
    )

    balance_before = balance

    balance += pnl

    # --------------------------------------------------------
    # HOLDING TIME
    # --------------------------------------------------------

    holding_minutes = (
        exit_time - entry_time
    ).total_seconds() / 60

    # --------------------------------------------------------
    # SAVE TRADE
    # --------------------------------------------------------

    trades.append({

        "trade_number":
            len(trades) + 1,

        "breakout_time":
            signal["breakout_time"],

        "structure_break_time":
            signal["structure_break_time"],

        "entry_time":
            entry_time,

        "direction":
            direction,

        "liquidity_price":
            signal["liquidity_price"],

        "structure_level":
            signal["structure_level"],

        "entry_price":
            entry,

        "stop_loss":
            sl,

        "take_profit":
            tp,

        "exit_time":
            exit_time,

        "exit_price":
            exit_price,

        "exit_reason":
            exit_reason,

        "quantity":
            quantity,

        "risk_amount":
            actual_risk,

        "pnl":
            pnl,

        "balance_before":
            balance_before,

        "balance_after":
            balance,

        "holding_minutes":
            holding_minutes,

        "bos_delay_minutes":
            signal["bos_delay_minutes"],

        "bos_distance":
            signal["bos_distance"],

        "retest_delay_minutes":
            signal["retest_delay_minutes"],

        "entry_distance":
            signal["entry_distance"],

        "signal_reason":
            signal["confirmation"]

    })

    # --------------------------------------------------------
    # BLOCK OVERLAPPING TRADE
    # --------------------------------------------------------

    used_until = exit_time


# ============================================================
# CREATE DATAFRAME
# ============================================================

trades_df = pd.DataFrame(
    trades
)


if trades_df.empty:

    print()
    print("NO TRADES WERE COMPLETED.")
    print("Check the confirmation and M1 data.")
    raise SystemExit


# ============================================================
# PERFORMANCE
# ============================================================

total_trades = len(
    trades_df
)

winning_trades = (
    trades_df["pnl"] > 0
).sum()

losing_trades = (
    trades_df["pnl"] < 0
).sum()

win_rate = (
    winning_trades
    / total_trades
    * 100
)

net_pnl = (
    trades_df["pnl"].sum()
)

final_balance = (
    trades_df["balance_after"].iloc[-1]
)

average_trade = (
    trades_df["pnl"].mean()
)


# ============================================================
# PROFIT FACTOR
# ============================================================

gross_profit = trades_df.loc[
    trades_df["pnl"] > 0,
    "pnl"
].sum()

gross_loss = abs(
    trades_df.loc[
        trades_df["pnl"] < 0,
        "pnl"
    ].sum()
)

if gross_loss > 0:

    profit_factor = (
        gross_profit
        / gross_loss
    )

else:

    profit_factor = np.inf


# ============================================================
# DRAWDOWN
# ============================================================

equity = trades_df[
    "balance_after"
]

peak = equity.cummax()

drawdown = (
    equity - peak
)

max_drawdown = (
    drawdown.min()
)

drawdown_percent = (
    max_drawdown
    / peak[drawdown.idxmin()]
    * 100
)


# ============================================================
# BUY / SELL
# ============================================================

buy_trades = trades_df[
    trades_df["direction"] == "BUY"
]

sell_trades = trades_df[
    trades_df["direction"] == "SELL"
]


def side_stats(data):

    if len(data) == 0:

        return (
            0,
            0,
            0
        )

    wins = (
        data["pnl"] > 0
    ).sum()

    rate = (
        wins
        / len(data)
        * 100
    )

    pnl = data["pnl"].sum()

    return (
        len(data),
        rate,
        pnl
    )


buy_count, buy_rate, buy_pnl = side_stats(
    buy_trades
)

sell_count, sell_rate, sell_pnl = side_stats(
    sell_trades
)


# ============================================================
# EXIT ANALYSIS
# ============================================================

tp_count = (
    trades_df["exit_reason"]
    == "TAKE_PROFIT"
).sum()

sl_count = (
    trades_df["exit_reason"]
    .isin([
        "STOP_LOSS",
        "SL_AND_TP_SAME_CANDLE"
    ])
).sum()

time_count = (
    trades_df["exit_reason"]
    == "TIME_EXIT"
).sum()


# ============================================================
# HOLDING TIME
# ============================================================

average_holding = (
    trades_df["holding_minutes"]
    .mean()
)

maximum_holding = (
    trades_df["holding_minutes"]
    .max()
)


# ============================================================
# STREAKS
# ============================================================

results = np.where(
    trades_df["pnl"] > 0,
    1,
    -1
)

max_win_streak = 0
max_loss_streak = 0

current_win = 0
current_loss = 0

for result in results:

    if result == 1:

        current_win += 1
        current_loss = 0

    else:

        current_loss += 1
        current_win = 0

    max_win_streak = max(
        max_win_streak,
        current_win
    )

    max_loss_streak = max(
        max_loss_streak,
        current_loss
    )


# ============================================================
# SAVE
# ============================================================

trades_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# PRINT RESULTS
# ============================================================

print()
print("=" * 60)
print("             MTF BACKTEST RESULTS")
print("=" * 60)

print()
print("ACCOUNT PERFORMANCE")
print("-" * 60)

print(
    f"Starting balance     : ${STARTING_BALANCE:,.2f}"
)

print(
    f"Final balance        : ${final_balance:,.2f}"
)

print(
    f"Net P/L              : ${net_pnl:,.2f}"
)

print(
    f"Return               : "
    f"{net_pnl / STARTING_BALANCE * 100:.2f}%"
)


print()
print("TRADE STATISTICS")
print("-" * 60)

print(
    f"Total trades         : {total_trades}"
)

print(
    f"Winning trades       : {winning_trades}"
)

print(
    f"Losing trades        : {losing_trades}"
)

print(
    f"Win rate             : {win_rate:.2f}%"
)

print(
    f"Profit factor        : {profit_factor:.2f}"
)

print(
    f"Average trade        : ${average_trade:.2f}"
)


print()
print("RISK")
print("-" * 60)

print(
    f"Maximum drawdown     : ${max_drawdown:.2f}"
)

print(
    f"Maximum drawdown %   : {drawdown_percent:.2f}%"
)

print(
    f"Max winning streak   : {max_win_streak}"
)

print(
    f"Max losing streak    : {max_loss_streak}"
)


print()
print("BUY vs SELL")
print("-" * 60)

print(
    f"BUY trades           : {buy_count}"
)

print(
    f"BUY win rate         : {buy_rate:.2f}%"
)

print(
    f"BUY P/L              : ${buy_pnl:.2f}"
)

print()

print(
    f"SELL trades          : {sell_count}"
)

print(
    f"SELL win rate        : {sell_rate:.2f}%"
)

print(
    f"SELL P/L             : ${sell_pnl:.2f}"
)


print()
print("EXIT ANALYSIS")
print("-" * 60)

print(
    f"Take Profit exits    : {tp_count}"
)

print(
    f"Stop Loss exits      : {sl_count}"
)

print(
    f"Time exits           : {time_count}"
)


print()
print("HOLDING TIME")
print("-" * 60)

print(
    f"Average holding     : "
    f"{average_holding:.1f} minutes"
)

print(
    f"Maximum holding     : "
    f"{maximum_holding:.1f} minutes"
)


print()
print("STRATEGY")
print("-" * 60)

print(
    "M30 Liquidity Breakout"
)

print(
    "+"
)

print(
    "M1 BOS"
)

print(
    "+"
)

print(
    "M1 Retest"
)

print(
    "+"
)

print(
    "RR 1:2"
)

print(
    "+"
)

print(
    "Risk 0.50%"
)


print()
print("=" * 60)

print(
    f"Saved trade log to:"
)

print(
    OUTPUT_FILE
)

print("=" * 60)
print()
