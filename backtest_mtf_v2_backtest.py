import pandas as pd
import numpy as np

# ============================================================
# SETTINGS
# ============================================================

SIGNALS_FILE = "data/processed/XAUUSDT-M1-high-probability-signals.csv"
MARKET_FILE = "data/processed/XAUUSDT-1m-combined.csv"

STARTING_BALANCE = 10000.0
RISK_PERCENT = 0.005
RR = 2.0
SL_BUFFER = 1.0

# ============================================================
# LOAD SIGNALS
# ============================================================

print("=" * 60)
print("       MTF LIQUIDITY + BOS + RETEST V2 BACKTEST")
print("=" * 60)

print("\nLoading filtered signals...")

signals = pd.read_csv(
    SIGNALS_FILE,
    parse_dates=[
        "breakout_time",
        "structure_break_time",
        "retest_time"
    ]
)

print(f"Filtered signals loaded: {len(signals)}")

# Entry is the retest entry price
signals["entry_time"] = signals["retest_time"]

# ============================================================
# LOAD MARKET DATA
# ============================================================

print("\nLoading 1-minute market data...")

df = pd.read_csv(
    MARKET_FILE,
    parse_dates=["open_time"]
)

df = df.sort_values("open_time").reset_index(drop=True)

print(f"1-minute candles loaded: {len(df):,}")

# ============================================================
# NORMALIZE COLUMN NAMES
# ============================================================

required = ["open_time", "high", "low", "close"]

for col in required:
    if col not in df.columns:
        raise ValueError(
            f"Missing required market column: {col}"
        )

# ============================================================
# BACKTEST
# ============================================================

balance = STARTING_BALANCE
trades = []

print("\nRunning V2 backtest...\n")

for _, signal in signals.iterrows():

    entry_time = signal["entry_time"]
    direction = signal["direction"]
    entry_price = float(signal["entry_price"])

    # --------------------------------------------------------
    # Find candles AFTER entry
    # --------------------------------------------------------

    future = df[df["open_time"] > entry_time].copy()

    if future.empty:
        continue

    # --------------------------------------------------------
    # Stop loss
    # --------------------------------------------------------

    if direction == "BULLISH_BREAKOUT":

        entry = entry_price

        # Use retest candle low
        retest_rows = df[
            df["open_time"] == entry_time
        ]

        if retest_rows.empty:
            continue

        retest_low = float(retest_rows.iloc[0]["low"])

        stop = retest_low - SL_BUFFER

        risk = entry - stop

        if risk <= 0:
            continue

        target = entry + risk * RR

        signal_name = "BUY"

    else:

        entry = entry_price

        retest_rows = df[
            df["open_time"] == entry_time
        ]

        if retest_rows.empty:
            continue

        retest_high = float(retest_rows.iloc[0]["high"])

        stop = retest_high + SL_BUFFER

        risk = stop - entry

        if risk <= 0:
            continue

        target = entry - risk * RR

        signal_name = "SELL"

    # --------------------------------------------------------
    # Position sizing
    # --------------------------------------------------------

    risk_amount = balance * RISK_PERCENT

    quantity = risk_amount / risk

    # --------------------------------------------------------
    # Check future candles
    # --------------------------------------------------------

    exit_time = None
    exit_price = None
    exit_reason = None

    for _, candle in future.iterrows():

        high = float(candle["high"])
        low = float(candle["low"])

        if signal_name == "BUY":

            # Conservative assumption:
            # if SL and TP happen in same candle,
            # assume SL happened first.

            if low <= stop:
                exit_time = candle["open_time"]
                exit_price = stop
                exit_reason = "STOP_LOSS"
                break

            if high >= target:
                exit_time = candle["open_time"]
                exit_price = target
                exit_reason = "TAKE_PROFIT"
                break

        else:

            if high >= stop:
                exit_time = candle["open_time"]
                exit_price = stop
                exit_reason = "STOP_LOSS"
                break

            if low <= target:
                exit_time = candle["open_time"]
                exit_price = target
                exit_reason = "TAKE_PROFIT"
                break

    if exit_time is None:
        continue

    # --------------------------------------------------------
    # P/L
    # --------------------------------------------------------

    if signal_name == "BUY":
        pnl = (exit_price - entry) * quantity
    else:
        pnl = (entry - exit_price) * quantity

    balance_before = balance

    balance += pnl

    holding_minutes = (
        exit_time - entry_time
    ).total_seconds() / 60

    trades.append({
        "trade_number": len(trades) + 1,
        "breakout_time": signal["breakout_time"],
        "entry_time": entry_time,
        "direction": signal_name,
        "liquidity_price": signal["liquidity_price"],
        "structure_level": signal["structure_level"],
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
        "bos_delay_minutes": signal["bos_delay_minutes"],
        "bos_distance": signal["bos_distance"],
        "retest_delay_minutes": signal["retest_delay_minutes"],
        "entry_distance": signal["entry_distance"],
        "signal_reason": signal["signal"]
    })

# ============================================================
# RESULTS
# ============================================================

results = pd.DataFrame(trades)

if results.empty:
    print("\nNo completed trades.")
    raise SystemExit

wins = results[results["pnl"] > 0]
losses = results[results["pnl"] <= 0]

total_trades = len(results)
winning_trades = len(wins)
losing_trades = len(losses)

win_rate = (
    winning_trades / total_trades * 100
)

gross_profit = wins["pnl"].sum()
gross_loss = abs(losses["pnl"].sum())

profit_factor = (
    gross_profit / gross_loss
    if gross_loss > 0
    else np.inf
)

average_trade = results["pnl"].mean()

# ============================================================
# DRAWdown
# ============================================================

equity = results["balance_after"]

running_max = equity.cummax()

drawdown = equity - running_max

max_drawdown = drawdown.min()

max_drawdown_pct = (
    max_drawdown /
    running_max[drawdown.idxmin()]
    * 100
)

# ============================================================
# STREAKS
# ============================================================

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

# ============================================================
# BUY / SELL
# ============================================================

buy = results[results["direction"] == "BUY"]
sell = results[results["direction"] == "SELL"]

# ============================================================
# PRINT RESULTS
# ============================================================

print("\n")
print("=" * 60)
print("             V2 BACKTEST RESULTS")
print("=" * 60)

print("\nACCOUNT PERFORMANCE")
print("-" * 60)

print(f"Starting balance     : ${STARTING_BALANCE:,.2f}")
print(f"Final balance        : ${balance:,.2f}")
print(f"Net P/L              : ${balance - STARTING_BALANCE:,.2f}")

print(
    f"Return               : "
    f"{(balance / STARTING_BALANCE - 1) * 100:.2f}%"
)

print("\nTRADE STATISTICS")
print("-" * 60)

print(f"Total trades         : {total_trades}")
print(f"Winning trades       : {winning_trades}")
print(f"Losing trades        : {losing_trades}")
print(f"Win rate             : {win_rate:.2f}%")
print(f"Profit factor        : {profit_factor:.2f}")
print(f"Average trade        : ${average_trade:.2f}")

print("\nRISK")
print("-" * 60)

print(f"Maximum drawdown     : ${max_drawdown:.2f}")
print(f"Maximum drawdown %   : {max_drawdown_pct:.2f}%")
print(f"Max winning streak   : {max_win_streak}")
print(f"Max losing streak    : {max_loss_streak}")

print("\nBUY vs SELL")
print("-" * 60)

if len(buy) > 0:
    print(
        f"BUY trades           : {len(buy)}"
    )
    print(
        f"BUY win rate         : "
        f"{(buy['pnl'] > 0).mean() * 100:.2f}%"
    )
    print(
        f"BUY P/L              : "
        f"${buy['pnl'].sum():.2f}"
    )

if len(sell) > 0:
    print(
        f"SELL trades          : {len(sell)}"
    )
    print(
        f"SELL win rate        : "
        f"{(sell['pnl'] > 0).mean() * 100:.2f}%"
    )
    print(
        f"SELL P/L             : "
        f"${sell['pnl'].sum():.2f}"
    )

print("\nEXIT ANALYSIS")
print("-" * 60)

print(
    f"Take Profit exits    : "
    f"{(results['exit_reason'] == 'TAKE_PROFIT').sum()}"
)

print(
    f"Stop Loss exits      : "
    f"{(results['exit_reason'] == 'STOP_LOSS').sum()}"
)

print("\nHOLDING TIME")
print("-" * 60)

print(
    f"Average holding      : "
    f"{results['holding_minutes'].mean():.1f} minutes"
)

print(
    f"Maximum holding      : "
    f"{results['holding_minutes'].max():.1f} minutes"
)

print("\nSTRATEGY")
print("-" * 60)

print("M30 Liquidity Breakout")
print("+ M1 BOS")
print("+ M1 Retest")
print("+ Probability Filters")
print("+ RR 1:2")
print("+ Risk 0.50%")

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

print("\n")
print("=" * 60)
print("Saved trade log to:")
print(OUTPUT_FILE)
print("=" * 60)