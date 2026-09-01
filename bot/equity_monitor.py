import csv
import os
from datetime import datetime, timezone


class EquityMonitor:

    def __init__(
        self,
        starting_balance=10000.0,
        equity_file="data/trades/equity_curve.csv"
    ):

        self.starting_balance = starting_balance

        self.realized_pnl = 0.0

        self.floating_pnl = 0.0

        self.current_equity = starting_balance

        self.equity_file = equity_file

        # ====================================================
        # EQUITY CURVE
        # ====================================================

        self.equity_history = [
            starting_balance
        ]

        # ====================================================
        # PEAK EQUITY
        # ====================================================

        self.peak_equity = starting_balance

        # ====================================================
        # DRAWDOWN
        # ====================================================

        self.current_drawdown = 0.0

        self.current_drawdown_percent = 0.0

        self.max_drawdown = 0.0

        self.max_drawdown_percent = 0.0

        # ====================================================
        # CREATE EQUITY JOURNAL
        # ====================================================

        self.initialize_equity_file()


    # ========================================================
    # INITIALIZE EQUITY CSV
    # ========================================================

    def initialize_equity_file(self):

        directory = os.path.dirname(
            self.equity_file
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True
            )

        if not os.path.exists(
            self.equity_file
        ):

            with open(
                self.equity_file,
                "w",
                newline=""
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "timestamp",
                    "equity",
                    "realized_pnl",
                    "floating_pnl",
                    "peak_equity",
                    "drawdown",
                    "drawdown_percent"
                ])


    # ========================================================
    # UPDATE AFTER TRADE CLOSES
    # ========================================================

    def update_realized_pnl(self, pnl):

        self.realized_pnl += float(pnl)

        # Trade is closed

        self.floating_pnl = 0.0

        self.current_equity = (
            self.starting_balance
            + self.realized_pnl
        )

        self.update_equity_tracking()

        self.save_equity_snapshot()

        self.print_equity()


    # ========================================================
    # UPDATE FLOATING P&L
    # ========================================================

    def update_floating_pnl(
        self,
        side,
        entry_price,
        current_price
    ):

        entry_price = float(entry_price)

        current_price = float(current_price)

        # ----------------------------------------------------
        # BUY
        # ----------------------------------------------------

        if side == "BUY":

            self.floating_pnl = (
                current_price - entry_price
            )

        # ----------------------------------------------------
        # SELL
        # ----------------------------------------------------

        elif side == "SELL":

            self.floating_pnl = (
                entry_price - current_price
            )

        else:

            self.floating_pnl = 0.0

        # ----------------------------------------------------
        # LIVE EQUITY
        # ----------------------------------------------------

        self.current_equity = (
            self.starting_balance
            + self.realized_pnl
            + self.floating_pnl
        )

        self.update_equity_tracking()

        self.save_equity_snapshot()

        self.print_live_equity(
            side,
            entry_price,
            current_price
        )


    # ========================================================
    # EQUITY TRACKING
    # ========================================================

    def update_equity_tracking(self):

        # ----------------------------------------------------
        # SAVE EQUITY IN MEMORY
        # ----------------------------------------------------

        self.equity_history.append(
            self.current_equity
        )

        # ----------------------------------------------------
        # UPDATE PEAK
        # ----------------------------------------------------

        if self.current_equity > self.peak_equity:

            self.peak_equity = (
                self.current_equity
            )

        # ----------------------------------------------------
        # CURRENT DRAWDOWN
        # ----------------------------------------------------

        self.current_drawdown = (
            self.peak_equity
            - self.current_equity
        )

        # ----------------------------------------------------
        # CURRENT DRAWDOWN %
        # ----------------------------------------------------

        if self.peak_equity > 0:

            self.current_drawdown_percent = (
                self.current_drawdown
                / self.peak_equity
            ) * 100

        else:

            self.current_drawdown_percent = 0.0

        # ----------------------------------------------------
        # MAXIMUM DRAWDOWN
        # ----------------------------------------------------

        if self.current_drawdown > self.max_drawdown:

            self.max_drawdown = (
                self.current_drawdown
            )

        # ----------------------------------------------------
        # MAXIMUM DRAWDOWN %
        # ----------------------------------------------------

        if (
            self.current_drawdown_percent
            > self.max_drawdown_percent
        ):

            self.max_drawdown_percent = (
                self.current_drawdown_percent
            )


    # ========================================================
    # SAVE EQUITY SNAPSHOT
    # ========================================================

    def save_equity_snapshot(self):

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        with open(
            self.equity_file,
            "a",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([

                timestamp,

                f"{self.current_equity:.4f}",

                f"{self.realized_pnl:.4f}",

                f"{self.floating_pnl:.4f}",

                f"{self.peak_equity:.4f}",

                f"{self.current_drawdown:.4f}",

                f"{self.current_drawdown_percent:.6f}"
            ])


    # ========================================================
    # GET CURRENT EQUITY
    # ========================================================

    def get_equity(self):

        return self.current_equity


    # ========================================================
    # GET REALIZED P&L
    # ========================================================

    def get_realized_pnl(self):

        return self.realized_pnl


    # ========================================================
    # GET FLOATING P&L
    # ========================================================

    def get_floating_pnl(self):

        return self.floating_pnl


    # ========================================================
    # GET PEAK EQUITY
    # ========================================================

    def get_peak_equity(self):

        return self.peak_equity


    # ========================================================
    # GET CURRENT DRAWDOWN
    # ========================================================

    def get_current_drawdown(self):

        return self.current_drawdown


    # ========================================================
    # GET MAXIMUM DRAWDOWN
    # ========================================================

    def get_max_drawdown(self):

        return self.max_drawdown


    # ========================================================
    # GET MAXIMUM DRAWDOWN %
    # ========================================================

    def get_max_drawdown_percent(self):

        return self.max_drawdown_percent


    # ========================================================
    # GET EQUITY HISTORY
    # ========================================================

    def get_equity_history(self):

        return self.equity_history


    # ========================================================
    # PRINT EQUITY AFTER TRADE CLOSE
    # ========================================================

    def print_equity(self):

        print()
        print("=" * 60)
        print("LIVE PAPER TRADING EQUITY")
        print("=" * 60)

        print(
            f"Starting Balance : "
            f"${self.starting_balance:.2f}"
        )

        print(
            f"Realized P&L     : "
            f"${self.realized_pnl:+.2f}"
        )

        print(
            f"Floating P&L     : "
            f"${self.floating_pnl:+.2f}"
        )

        print(
            f"Current Equity   : "
            f"${self.current_equity:.2f}"
        )

        print(
            f"Peak Equity      : "
            f"${self.peak_equity:.2f}"
        )

        print(
            f"Drawdown         : "
            f"${self.current_drawdown:.2f}"
        )

        print(
            f"Drawdown %       : "
            f"{self.current_drawdown_percent:.2f}%"
        )

        print(
            f"Max Drawdown     : "
            f"${self.max_drawdown:.2f}"
        )

        print(
            f"Max Drawdown %   : "
            f"{self.max_drawdown_percent:.2f}%"
        )

        print("=" * 60)


    # ========================================================
    # PRINT LIVE EQUITY
    # ========================================================

    def print_live_equity(
        self,
        side,
        entry_price,
        current_price
    ):

        print()
        print("=" * 60)
        print("LIVE PAPER TRADING EQUITY")
        print("=" * 60)

        print(
            f"Side             : "
            f"{side}"
        )

        print(
            f"Entry Price      : "
            f"{entry_price:.2f}"
        )

        print(
            f"Current Price    : "
            f"{current_price:.2f}"
        )

        print(
            f"Starting Balance : "
            f"${self.starting_balance:.2f}"
        )

        print(
            f"Realized P&L     : "
            f"${self.realized_pnl:+.2f}"
        )

        print(
            f"Floating P&L     : "
            f"${self.floating_pnl:+.2f}"
        )

        print(
            f"Current Equity   : "
            f"${self.current_equity:.2f}"
        )

        print(
            f"Peak Equity      : "
            f"${self.peak_equity:.2f}"
        )

        print(
            f"Drawdown         : "
            f"${self.current_drawdown:.2f}"
        )

        print(
            f"Drawdown %       : "
            f"{self.current_drawdown_percent:.2f}%"
        )

        print(
            f"Max Drawdown     : "
            f"${self.max_drawdown:.2f}"
        )

        print(
            f"Max Drawdown %   : "
            f"{self.max_drawdown_percent:.2f}%"
        )

        print("=" * 60)