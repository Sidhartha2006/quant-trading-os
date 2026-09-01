import pandas as pd
import numpy as np

# ============================================================
# V2 BACKTEST
# ============================================================

SIGNALS_FILE = "data/processed/XAUUSDT-M1-high-probability-signals.csv"
DATA_FILE = "data/processed/XAUUSDT-1m-combined.csv"

INITIAL_BALANCE = 10000.0
RISK_PERCENT = 0.005
RR = 2.0
SL_BUFFER = 1.0


print("=" * 60)
print("       V2 HIGH-PROBABILITY BACKTEST")
print("=" * 60)

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------

signals = pd.read_csv(
    SIGNALS_FILE,
    parse_dates=[
        "breakout_time",
        "structure_break_time",
        "entry_time"
    ]
)

df = pd.read_csv(
    DATA_FILE,
    parse_dates=["open_time"]
)

df = df.sort_values("open_time").reset_index(drop=True)

signals = signals.sort_values("entry_time").reset_index(drop=True)

print(f"Signals loaded : {len(signals)}")
print(f"Market candles : {len(df)}")

# ------------------------------------------------------------
# BACKTEST
# ------------------------------------------------------------

balance = INITIAL_BALANCE
trades = []

for _, signal in signals.iterrows():

    entry_time = pd.Timestamp(signal["entry_time"])
    direction = signal["direction"]

    # Find entry candle
    future = df[df["open_time"] >= entry_time]

    if future.empty:
        continue

    entry_candle = future.iloc[0]

    entry = float(signal["entry_price"])

    # --------------------------------------------------------
    # STOP / TARGET
    # --------------------------------------------------------

    if direction == "BUY":

        stop = float(entry_candle["low"]) - SL_BUFFER
        risk = entry - stop

        if risk <= 0:
            continue

        target = entry + risk * RR

    else:

        stop = float(entry_candle["high"]) + SL_BUFFER
        risk = stop - entry

        if risk <= 0:
            continue

        target = entry - risk * RR

    # Risk fixed at 0.5% of current balance
    risk_amount = balance * RISK_PERCENT

    quantity = risk_amount / risk

    # --------------------------------------------------------
    # FUTURE CANDLES
    # --------------------------------------------------------

    future = future.iloc[1:]

    exit_price = None
    exit_reason = None
    exit_time = None

    for _, candle in future.iterrows():

        high = float(candle["high"])
        low = float(candle["low"])

        if direction == "BUY":

            # Conservative assumption:
            # if both TP and SL occur in same candle,
            # assume SL happens first.
            if low <= stop:
                exit_price = stop
                exit_reason = "STOP_LOSS"
                exit_time = candle["open_time"]
                break

            if high >= target:
                exit_price = target
                exit_reason = "TAKE_PROFIT"
                exit_time = candle["open_time"]
                break

        else:

            if high >= stop:
                exit_price = stop
                exit_reason = "STOP_LOSS"
                exit_time = candle["open_time"]
                break

            if low <= target:
                exit_price = target
                exit_reason = "TAKE_PROFIT"
                exit_time = candle["open_time"]
                break

    if exit_price is None:
        continue

    # --------------------------------------------------------
    # P/L
    # --------------------------------------------------------

    if direction == "BUY":
        pnl = (exit_price - entry) * quantity
    else:
        pnl = (entry - exit_price) * quantity

    balance_before = balance
    balance += pnl

    holding_minutes = (
        exit_time - entry_time
    ).total_seconds() / 60

    trades.append({
        "entry_time": entry_time,
        "direction": direction,
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit": target,
        "exit_time": exit_time,
        "exit_price": exit_price,
        "exit_reason": exit_reason,
        "quantity": quantity,
        "risk_amount": risk_amount,
        "pnl": pnl,
        "balance_before": balance_before,
        "balance_after": balance,
        "holding_minutes": holding_minutes,
        "bos_delay_minutes": signal.get(
            "bos_delay_minutes", np.nan
        ),
        "retest_delay_minutes": signal.get(
            "retest_delay_minutes", np.nan
        )
    })


# ============================================================
# RESULTS
# ============================================================

results = pd.DataFrame(trades)

if results.empty:
    print("No completed trades.")
    exit()

wins = results[results["pnl"] > 0]
losses = results[results["pnl"] <= 0]

total_trades = len(results)
winning_trades = len(wins)
losing_trades = len(losses)

win_rate = winning_trades / total_trades * 100

gross_profit = wins["pnl"].sum()
gross_loss = abs(losses["pnl"].sum())

profit_factor = (
    gross_profit / gross_loss
    if gross_loss > 0
    else float("inf")
)

net_profit = results["pnl"].sum()

avg_trade = results["pnl"].mean()

# ------------------------------------------------------------
# DRAW DOWN
# ------------------------------------------------------------

equity = results["balance_after"]

running_max = equity.cummax()

drawdown = equity - running_max

max_drawdown = drawdown.min()

max_drawdown_percent = (
    max_drawdown / INITIAL_BALANCE * 100
)

# ------------------------------------------------------------
# STREAKS
# ------------------------------------------------------------

win_flags = results["pnl"] > 0

max_win_streak = 0
max_loss_streak = 0

current_win = 0
current_loss = 0

for win in win_flags:

    if win:
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

# ------------------------------------------------------------
# BUY / SELL
# ------------------------------------------------------------

buy = results[results["direction"] == "BUY"]
sell = results[results["direction"] == "SELL"]

buy_win_rate = (
    (buy["pnl"] > 0).mean() * 100
    if len(buy)
    else 0
)

sell_win_rate = (
    (sell["pnl"] > 0).mean() * 100
    if len(sell)
    else 0
)

# ============================================================
# PRINT
# ============================================================

print()
print("=" * 60)
print("              V2 BACKTEST RESULTS")
print("=" * 60)

print()
print("ACCOUNT PERFORMANCE")
print("-" * 60)

print(f"Starting balance : ${INITIAL_BALANCE:,.2f}")
print(f"Final balance    : ${balance:,.2f}")
print(f"Net P/L          : ${net_profit:,.2f}")

print(
    f"Return           : "
    f"{net_profit / INITIAL_BALANCE * 100:.2f}%"
)

print()
print("TRADE STATISTICS")
print("-" * 60)

print(f"Total trades     : {total_trades}")
print(f"Winning trades   : {winning_trades}")
print(f"Losing trades    : {losing_trades}")
print(f"Win rate         : {win_rate:.2f}%")
print(f"Profit factor    : {profit_factor:.2f}")
print(f"Average trade    : ${avg_trade:.2f}")

print()
print("RISK")
print("-" * 60)

print(f"Maximum drawdown : ${max_drawdown:.2f}")
print(f"Maximum DD %     : {max_drawdown_percent:.2f}%")
print(f"Max win streak   : {max_win_streak}")
print(f"Max loss streak  : {max_loss_streak}")

print()
print("BUY vs SELL")
print("-" * 60)

print(
    f"BUY  : {len(buy):2d} trades | "
    f"Win rate {buy_win_rate:.2f}% | "
    f"P/L ${buy['pnl'].sum():.2f}"
)

print(
    f"SELL : {len(sell):2d} trades | "
    f"Win rate {sell_win_rate:.2f}% | "
    f"P/L ${sell['pnl'].sum():.2f}"
)

print()
print("EXIT ANALYSIS")
print("-" * 60)

print(
    f"Take Profit : "
    f"{(results['exit_reason'] == 'TAKE_PROFIT').sum()}"
)

print(
    f"Stop Loss   : "
    f"{(results['exit_reason'] == 'STOP_LOSS').sum()}"
)

print()
print("HOLDING TIME")
print("-" * 60)

print(
    f"Average holding : "
    f"{results['holding_minutes'].mean():.1f} minutes"
)

print(
    f"Maximum holding : "
    f"{results['holding_minutes'].max():.1f} minutes"
)

# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE = (
    "data/processed/"
    "mtf_v2_backtest_trades.csv"
)

results.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 60)
print(f"Saved trade log to:")
print(OUTPUT_FILE)
print("=" * 60)
