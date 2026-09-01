import csv
import os


# ============================================================
# CONFIG
# ============================================================

TRADE_FILE = "data/trades/paper_trades.csv"

STARTING_BALANCE = 10000.0


# ============================================================
# LOAD TRADES
# ============================================================

def load_trades():

    if not os.path.exists(TRADE_FILE):

        print()
        print("=" * 60)
        print("NO TRADE JOURNAL FOUND")
        print("=" * 60)

        print(
            f"File not found: {TRADE_FILE}"
        )

        print("=" * 60)

        return []

    with open(
        TRADE_FILE,
        "r",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        trades = list(reader)

    return trades


# ============================================================
# VALIDATION STATISTICS
# ============================================================

def calculate_statistics(trades):

    if not trades:
        return None

    total_trades = 0

    wins = 0
    losses = 0

    total_pnl = 0.0

    winning_pnl = 0.0
    losing_pnl = 0.0

    largest_win = None
    largest_loss = None

    total_risk_reward = 0.0

    buy_trades = 0
    buy_wins = 0
    buy_pnl = 0.0

    sell_trades = 0
    sell_wins = 0
    sell_pnl = 0.0

    # ========================================================
    # STREAKS
    # ========================================================

    current_win_streak = 0
    current_loss_streak = 0

    max_win_streak = 0
    max_loss_streak = 0

    # ========================================================
    # EQUITY
    # ========================================================

    equity = STARTING_BALANCE

    peak_equity = STARTING_BALANCE

    max_drawdown = 0.0

    equity_curve = []

    # ========================================================
    # PROCESS EACH TRADE
    # ========================================================

    for trade in trades:

        # ----------------------------------------------------
        # SAFETY CHECK
        # ----------------------------------------------------

        try:

            status = trade["status"].strip().upper()

            pnl = float(
                trade["pnl"]
            )

            risk_reward = float(
                trade["risk_reward"]
            )

            side = trade["side"].strip().upper()

        except (KeyError, ValueError, TypeError):

            print(
                "WARNING → Skipping invalid trade row"
            )

            continue

        # ----------------------------------------------------
        # ONLY COMPLETED TRADES
        # ----------------------------------------------------

        if status not in ["WIN", "LOSS"]:

            continue

        total_trades += 1

        total_pnl += pnl

        total_risk_reward += risk_reward

        # ====================================================
        # EQUITY CURVE
        # ====================================================

        equity += pnl

        equity_curve.append(equity)

        # ----------------------------------------------------
        # UPDATE PEAK
        # ----------------------------------------------------

        if equity > peak_equity:

            peak_equity = equity

        # ----------------------------------------------------
        # DRAWdown
        # ----------------------------------------------------

        drawdown = peak_equity - equity

        if drawdown > max_drawdown:

            max_drawdown = drawdown

        # ====================================================
        # WIN
        # ====================================================

        if status == "WIN":

            wins += 1

            winning_pnl += pnl

            # Win streak

            current_win_streak += 1
            current_loss_streak = 0

            if current_win_streak > max_win_streak:

                max_win_streak = current_win_streak

            # Largest win

            if (
                largest_win is None
                or pnl > largest_win
            ):

                largest_win = pnl

        # ====================================================
        # LOSS
        # ====================================================

        elif status == "LOSS":

            losses += 1

            losing_pnl += pnl

            # Loss streak

            current_loss_streak += 1
            current_win_streak = 0

            if current_loss_streak > max_loss_streak:

                max_loss_streak = current_loss_streak

            # Largest loss

            if (
                largest_loss is None
                or pnl < largest_loss
            ):

                largest_loss = pnl

        # ====================================================
        # BUY / SELL
        # ====================================================

        if side == "BUY":

            buy_trades += 1

            buy_pnl += pnl

            if status == "WIN":

                buy_wins += 1

        elif side == "SELL":

            sell_trades += 1

            sell_pnl += pnl

            if status == "WIN":

                sell_wins += 1

    # ========================================================
    # NO VALID TRADES
    # ========================================================

    if total_trades == 0:

        return None

    # ========================================================
    # WIN RATE
    # ========================================================

    win_rate = (
        wins / total_trades
    ) * 100

    # ========================================================
    # AVERAGE P&L
    # ========================================================

    average_pnl = (
        total_pnl / total_trades
    )

    # ========================================================
    # AVERAGE WIN
    # ========================================================

    if wins > 0:

        average_win = (
            winning_pnl / wins
        )

    else:

        average_win = 0.0

    # ========================================================
    # AVERAGE LOSS
    # ========================================================

    if losses > 0:

        average_loss = (
            losing_pnl / losses
        )

    else:

        average_loss = 0.0

    # ========================================================
    # PROFIT FACTOR
    # ========================================================

    if losing_pnl != 0:

        profit_factor = (
            winning_pnl
            / abs(losing_pnl)
        )

    else:

        profit_factor = float("inf")

    # ========================================================
    # AVERAGE R:R
    # ========================================================

    average_risk_reward = (
        total_risk_reward
        / total_trades
    )

    # ========================================================
    # EXPECTANCY
    # ========================================================

    expectancy = average_pnl

    # ========================================================
    # BUY WIN RATE
    # ========================================================

    if buy_trades > 0:

        buy_win_rate = (
            buy_wins
            / buy_trades
        ) * 100

    else:

        buy_win_rate = 0.0

    # ========================================================
    # SELL WIN RATE
    # ========================================================

    if sell_trades > 0:

        sell_win_rate = (
            sell_wins
            / sell_trades
        ) * 100

    else:

        sell_win_rate = 0.0

    # ========================================================
    # RETURN RESULTS
    # ========================================================

    return {

        "total_trades":
            total_trades,

        "wins":
            wins,

        "losses":
            losses,

        "win_rate":
            win_rate,

        "total_pnl":
            total_pnl,

        "average_pnl":
            average_pnl,

        "average_win":
            average_win,

        "average_loss":
            average_loss,

        "profit_factor":
            profit_factor,

        "average_risk_reward":
            average_risk_reward,

        "expectancy":
            expectancy,

        "largest_win":
            largest_win,

        "largest_loss":
            largest_loss,

        "max_win_streak":
            max_win_streak,

        "max_loss_streak":
            max_loss_streak,

        "buy_trades":
            buy_trades,

        "buy_wins":
            buy_wins,

        "buy_win_rate":
            buy_win_rate,

        "buy_pnl":
            buy_pnl,

        "sell_trades":
            sell_trades,

        "sell_wins":
            sell_wins,

        "sell_win_rate":
            sell_win_rate,

        "sell_pnl":
            sell_pnl,

        "starting_balance":
            STARTING_BALANCE,

        "final_balance":
            equity,

        "max_drawdown":
            max_drawdown,

        "equity_curve":
            equity_curve
    }


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(stats):

    print()
    print("=" * 60)
    print("TRADING STRATEGY VALIDATION REPORT")
    print("=" * 60)

    # ========================================================
    # BASIC PERFORMANCE
    # ========================================================

    print()
    print("PERFORMANCE")
    print("-" * 60)

    print(
        f"Total Trades       : "
        f"{stats['total_trades']}"
    )

    print(
        f"Winning Trades     : "
        f"{stats['wins']}"
    )

    print(
        f"Losing Trades      : "
        f"{stats['losses']}"
    )

    print(
        f"Win Rate           : "
        f"{stats['win_rate']:.2f}%"
    )

    print(
        f"Total P&L          : "
        f"{stats['total_pnl']:.2f}"
    )

    print(
        f"Average P&L        : "
        f"{stats['average_pnl']:.2f}"
    )

    print(
        f"Average Win        : "
        f"{stats['average_win']:.2f}"
    )

    print(
        f"Average Loss       : "
        f"{stats['average_loss']:.2f}"
    )

    # ========================================================
    # RISK
    # ========================================================

    print()
    print("RISK ANALYSIS")
    print("-" * 60)

    if stats["profit_factor"] == float("inf"):

        print(
            "Profit Factor      : ∞"
        )

    else:

        print(
            f"Profit Factor      : "
            f"{stats['profit_factor']:.2f}"
        )

    print(
        f"Average R:R        : "
        f"1:{stats['average_risk_reward']:.2f}"
    )

    print(
        f"Expectancy         : "
        f"{stats['expectancy']:.2f}"
    )

    print(
        f"Largest Win        : "
        f"{stats['largest_win']:.2f}"
    )

    print(
        f"Largest Loss       : "
        f"{stats['largest_loss']:.2f}"
    )

    print(
        f"Max Drawdown       : "
        f"{stats['max_drawdown']:.2f}"
    )

    # ========================================================
    # STREAKS
    # ========================================================

    print()
    print("STREAK ANALYSIS")
    print("-" * 60)

    print(
        f"Max Winning Streak : "
        f"{stats['max_win_streak']}"
    )

    print(
        f"Max Losing Streak  : "
        f"{stats['max_loss_streak']}"
    )

    # ========================================================
    # EQUITY
    # ========================================================

    print()
    print("EQUITY")
    print("-" * 60)

    print(
        f"Starting Balance   : "
        f"{stats['starting_balance']:.2f}"
    )

    print(
        f"Final Balance      : "
        f"{stats['final_balance']:.2f}"
    )

    print(
        f"Net Change         : "
        f"{stats['final_balance'] - stats['starting_balance']:.2f}"
    )

    # ========================================================
    # BUY
    # ========================================================

    print()
    print("BUY PERFORMANCE")
    print("-" * 60)

    print(
        f"BUY Trades         : "
        f"{stats['buy_trades']}"
    )

    print(
        f"BUY Wins           : "
        f"{stats['buy_wins']}"
    )

    print(
        f"BUY Win Rate       : "
        f"{stats['buy_win_rate']:.2f}%"
    )

    print(
        f"BUY P&L            : "
        f"{stats['buy_pnl']:.2f}"
    )

    # ========================================================
    # SELL
    # ========================================================

    print()
    print("SELL PERFORMANCE")
    print("-" * 60)

    print(
        f"SELL Trades        : "
        f"{stats['sell_trades']}"
    )

    print(
        f"SELL Wins          : "
        f"{stats['sell_wins']}"
    )

    print(
        f"SELL Win Rate      : "
        f"{stats['sell_win_rate']:.2f}%"
    )

    print(
        f"SELL P&L           : "
        f"{stats['sell_pnl']:.2f}"
    )

    # ========================================================
    # SAMPLE SIZE
    # ========================================================

    print()
    print("VALIDATION SAMPLE")
    print("-" * 60)

    if stats["total_trades"] < 20:

        remaining = (
            20 - stats["total_trades"]
        )

        print(
            f"Trades Collected   : "
            f"{stats['total_trades']}/20"
        )

        print(
            f"Trades Remaining   : "
            f"{remaining}"
        )

        print(
            "STATUS             : "
            "COLLECT MORE TRADES"
        )

    else:

        print(
            f"Trades Collected   : "
            f"{stats['total_trades']}"
        )

        print(
            "STATUS             : "
            "20+ TRADE SAMPLE"
        )

    print("=" * 60)


# ============================================================
# PRINT EQUITY CURVE
# ============================================================

def print_equity_curve(stats):

    equity_curve = stats["equity_curve"]

    if not equity_curve:

        return

    print()
    print("=" * 60)
    print("EQUITY CURVE")
    print("=" * 60)

    for index, equity in enumerate(
        equity_curve,
        start=1
    ):

        print(
            f"Trade {index:<4} → "
            f"Equity : {equity:.2f}"
        )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    trades = load_trades()

    stats = calculate_statistics(
        trades
    )

    if stats is not None:

        print_report(
            stats
        )

        print_equity_curve(
            stats
        )