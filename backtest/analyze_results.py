import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================
# FILES
# ============================================================

TRADES_FILE = Path("data/processed/backtest_trades.csv")
SIGNALS_FILE = Path("data/processed/XAUUSDT-5m-with-signals.csv")

# ============================================================
# LOAD
# ============================================================

trades = pd.read_csv(TRADES_FILE, parse_dates=["entry_time", "exit_time"])
signals = pd.read_csv(SIGNALS_FILE, parse_dates=["open_time"])

if trades.empty:
    print("No trades found.")
    exit()

# ============================================================
# BASIC METRICS
# ============================================================

starting_balance = 10000.0

final_balance = trades["balance_after"].iloc[-1]

net_profit = final_balance - starting_balance

wins = trades[trades["pnl_dollars"] > 0]
losses = trades[trades["pnl_dollars"] < 0]

winning_trades = len(wins)
losing_trades = len(losses)
total_trades = len(trades)

win_rate = (
    winning_trades / total_trades * 100
    if total_trades > 0 else 0
)

gross_profit = wins["pnl_dollars"].sum()
gross_loss = abs(losses["pnl_dollars"].sum())

profit_factor = (
    gross_profit / gross_loss
    if gross_loss > 0 else np.inf
)

average_trade = trades["pnl_dollars"].mean()

# ============================================================
# MAX DRAWDOWN
# ============================================================

equity = trades["balance_after"]

running_peak = equity.cummax()

drawdown_dollars = equity - running_peak

drawdown_pct = (
    drawdown_dollars / running_peak * 100
)

max_drawdown_dollars = drawdown_dollars.min()

max_drawdown_pct = drawdown_pct.min()

# ============================================================
# LONG / SHORT ANALYSIS
# ============================================================

buy_trades = trades[trades["signal"] == "BUY"]
sell_trades = trades[trades["signal"] == "SELL"]

buy_wins = (buy_trades["pnl_dollars"] > 0).sum()
sell_wins = (sell_trades["pnl_dollars"] > 0).sum()

buy_win_rate = (
    buy_wins / len(buy_trades) * 100
    if len(buy_trades) else 0
)

sell_win_rate = (
    sell_wins / len(sell_trades) * 100
    if len(sell_trades) else 0
)

# ============================================================
# EXIT ANALYSIS
# ============================================================

tp_trades = trades[trades["exit_reason"] == "TP"]
sl_trades = trades[trades["exit_reason"] == "SL"]

tp_count = len(tp_trades)
sl_count = len(sl_trades)

# ============================================================
# HOLDING TIME
# ============================================================

trades["holding_minutes"] = (
    trades["exit_time"] - trades["entry_time"]
).dt.total_seconds() / 60

average_holding = trades["holding_minutes"].mean()

max_holding = trades["holding_minutes"].max()

# ============================================================
# CONSECUTIVE LOSSES / WINS
# ============================================================

results = np.where(
    trades["pnl_dollars"] > 0,
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

        max_win_streak = max(
            max_win_streak,
            current_win
        )

    else:

        current_loss += 1
        current_win = 0

        max_loss_streak = max(
            max_loss_streak,
            current_loss
        )

# ============================================================
# CONNECT TRADES TO SIGNALS
# ============================================================

# Entry happens on the candle AFTER the signal.
# Therefore signal_time = entry_time - 5 minutes.

trades["signal_time"] = (
    trades["entry_time"] - pd.Timedelta(minutes=5)
)

signal_columns = [
    "open_time",
    "touch_number",
    "zone_price",
    "zone_low",
    "zone_high",
    "signal_reason"
]

available_columns = [
    c for c in signal_columns
    if c in signals.columns
]

if "open_time" in available_columns:

    signal_info = signals[available_columns].copy()

    signal_info = signal_info.rename(
        columns={"open_time": "signal_time"}
    )

    trades = trades.merge(
        signal_info,
        on="signal_time",
        how="left"
    )

# ============================================================
# TOUCH NUMBER ANALYSIS
# ============================================================

if "touch_number" in trades.columns:

    touch_data = trades.dropna(
        subset=["touch_number"]
    ).copy()

else:

    touch_data = pd.DataFrame()

# ============================================================
# PRINT REPORT
# ============================================================

print()
print("=" * 60)
print("              BACKTEST ANALYSIS")
print("=" * 60)

print()

print("ACCOUNT PERFORMANCE")
print("-" * 60)

print(
    f"Starting balance     : ${starting_balance:,.2f}"
)

print(
    f"Final balance        : ${final_balance:,.2f}"
)

print(
    f"Net P/L              : ${net_profit:,.2f}"
)

print(
    f"Return               : "
    f"{net_profit / starting_balance * 100:.2f}%"
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
    f"Average trade       : ${average_trade:.2f}"
)

print()

print("RISK")
print("-" * 60)

print(
    f"Maximum drawdown     : "
    f"${max_drawdown_dollars:,.2f}"
)

print(
    f"Maximum drawdown %   : "
    f"{max_drawdown_pct:.2f}%"
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
    f"BUY trades           : {len(buy_trades)}"
)

print(
    f"BUY win rate         : {buy_win_rate:.2f}%"
)

print(
    f"BUY P/L              : "
    f"${buy_trades['pnl_dollars'].sum():,.2f}"
)

print()

print(
    f"SELL trades          : {len(sell_trades)}"
)

print(
    f"SELL win rate        : {sell_win_rate:.2f}%"
)

print(
    f"SELL P/L             : "
    f"${sell_trades['pnl_dollars'].sum():,.2f}"
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

print()

print("HOLDING TIME")
print("-" * 60)

print(
    f"Average holding     : "
    f"{average_holding:.1f} minutes"
)

print(
    f"Maximum holding     : "
    f"{max_holding:.1f} minutes"
)

# ============================================================
# TOUCH ANALYSIS
# ============================================================

if not touch_data.empty:

    print()

    print("PERFORMANCE BY TOUCH NUMBER")
    print("-" * 60)

    touch_summary = (
        touch_data
        .groupby("touch_number")
        .agg(
            trades=("pnl_dollars", "count"),
            win_rate=(
                "pnl_dollars",
                lambda x: (x > 0).mean() * 100
            ),
            pnl=("pnl_dollars", "sum"),
            avg_trade=("pnl_dollars", "mean")
        )
        .reset_index()
    )

    print(
        touch_summary.to_string(
            index=False
        )
    )

else:

    print()

    print(
        "Touch-number analysis unavailable."
    )

# ============================================================
# SIGNAL REASON ANALYSIS
# ============================================================

if "signal_reason" in trades.columns:

    print()

    print("SIGNAL REASON PERFORMANCE")
    print("-" * 60)

    reason_summary = (
        trades
        .dropna(subset=["signal_reason"])
        .groupby("signal_reason")
        .agg(
            trades=("pnl_dollars", "count"),
            win_rate=(
                "pnl_dollars",
                lambda x: (x > 0).mean() * 100
            ),
            pnl=("pnl_dollars", "sum"),
            avg_trade=("pnl_dollars", "mean")
        )
        .reset_index()
    )

    print(
        reason_summary.to_string(
            index=False
        )
    )

# ============================================================
# SAVE ENRICHED TRADES
# ============================================================

OUTPUT_FILE = Path(
    "data/processed/backtest_trades_analyzed.csv"
)

trades.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 60)
print("              ANALYSIS COMPLETE")
print("=" * 60)

print(
    f"Saved detailed analysis to:"
)

print(
    OUTPUT_FILE
)

print("=" * 60)