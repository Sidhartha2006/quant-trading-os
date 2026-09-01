import csv
import os


class PaperTrade:

    def __init__(self, starting_equity=10000.0):

        self.active_trade = None

        # ====================================================
        # ACCOUNT
        # ====================================================

        self.starting_equity = float(
            starting_equity
        )

        self.realized_pnl = 0.0

        # Count completed trades
        self.trade_number = 0


    # ========================================================
    # OPEN PAPER TRADE
    # ========================================================

    def open_trade(self, trade):

        quantity = float(
            trade.get(
                "quantity",
                0.5
            )
        )

        self.active_trade = {

            "side": trade["side"],

            "entry": float(
                trade["entry"]
            ),

            "stop_loss": float(
                trade["stop_loss"]
            ),

            "take_profit": float(
                trade["take_profit"]
            ),

            "risk": float(
                trade["risk"]
            ),

            "reward": float(
                trade["reward"]
            ),

            "risk_reward": float(
                trade["risk_reward"]
            ),

            "quantity": quantity,

            "entry_time":
                trade["timestamp"],

            "exit_time": None,

            "exit_price": None,

            "status": "OPEN",

            "pnl": 0.0
        }

        print()
        print("=" * 60)
        print("PAPER TRADE OPENED")
        print("=" * 60)

        print(
            "Side        :",
            self.active_trade["side"]
        )

        print(
            "Entry       :",
            f"{self.active_trade['entry']:.2f}"
        )

        print(
            "Stop Loss   :",
            f"{self.active_trade['stop_loss']:.2f}"
        )

        print(
            "Take Profit :",
            f"{self.active_trade['take_profit']:.2f}"
        )

        print(
            "Quantity    :",
            f"{self.active_trade['quantity']:.2f} lots"
        )

        print(
            "Risk        :",
            f"{self.active_trade['risk']:.2f}"
        )

        print(
            "Reward      :",
            f"{self.active_trade['reward']:.2f}"
        )

        print(
            "Risk/Reward :",
            f"1:{self.active_trade['risk_reward']:.2f}"
        )

        print(
            "Entry Time  :",
            self.active_trade["entry_time"]
        )

        print(
            "Starting Equity :",
            f"${self.starting_equity:.2f}"
        )

        print("=" * 60)


    # ========================================================
    # CALCULATE UNREALIZED P&L
    # ========================================================

    def calculate_unrealized_pnl(
        self,
        current_price
    ):

        if self.active_trade is None:

            return 0.0

        entry = float(
            self.active_trade["entry"]
        )

        current_price = float(
            current_price
        )

        quantity = float(
            self.active_trade["quantity"]
        )

        side = self.active_trade["side"]


        # ====================================================
        # BUY
        # ====================================================

        if side == "BUY":

            price_difference = (
                current_price - entry
            )


        # ====================================================
        # SELL
        # ====================================================

        else:

            price_difference = (
                entry - current_price
            )


        # ====================================================
        # PROJECT PAPER MODEL
        #
        # P&L = price movement × quantity
        # ====================================================

        pnl = (
            price_difference
            * quantity
        )

        return pnl


    # ========================================================
    # SHOW LIVE EQUITY
    # ========================================================

    def show_live_equity(
        self,
        current_price
    ):

        if self.active_trade is None:

            return

        current_price = float(
            current_price
        )

        unrealized_pnl = (
            self.calculate_unrealized_pnl(
                current_price
            )
        )

        live_equity = (
            self.starting_equity
            + self.realized_pnl
            + unrealized_pnl
        )

        print()
        print("=" * 60)
        print("LIVE PAPER TRADE")
        print("=" * 60)

        print(
            "Side           :",
            self.active_trade["side"]
        )

        print(
            "Entry          :",
            f"{self.active_trade['entry']:.2f}"
        )

        print(
            "Current Price  :",
            f"{current_price:.2f}"
        )

        print(
            "Stop Loss      :",
            f"{self.active_trade['stop_loss']:.2f}"
        )

        print(
            "Take Profit    :",
            f"{self.active_trade['take_profit']:.2f}"
        )

        print(
            "Quantity       :",
            f"{self.active_trade['quantity']:.2f} lots"
        )

        print(
            "Unrealized P&L :",
            f"${unrealized_pnl:+.2f}"
        )

        print(
            "Realized P&L   :",
            f"${self.realized_pnl:+.2f}"
        )

        print(
            "Live Equity    :",
            f"${live_equity:.2f}"
        )

        print(
            "Status         : RUNNING"
        )

        print("=" * 60)


    # ========================================================
    # CHECK ACTIVE TRADE
    # ========================================================

    def check_trade(self, candle):

        if self.active_trade is None:

            return None

        if self.active_trade["status"] != "OPEN":

            return None

        high = float(
            candle["high"]
        )

        low = float(
            candle["low"]
        )

        side = self.active_trade["side"]

        stop_loss = float(
            self.active_trade["stop_loss"]
        )

        take_profit = float(
            self.active_trade["take_profit"]
        )


        # ====================================================
        # BUY
        # ====================================================

        if side == "BUY":

            if low <= stop_loss:

                return self.close_trade(

                    stop_loss,

                    "LOSS",

                    candle["timestamp"]
                )


            if high >= take_profit:

                return self.close_trade(

                    take_profit,

                    "WIN",

                    candle["timestamp"]
                )


        # ====================================================
        # SELL
        # ====================================================

        elif side == "SELL":

            if high >= stop_loss:

                return self.close_trade(

                    stop_loss,

                    "LOSS",

                    candle["timestamp"]
                )


            if low <= take_profit:

                return self.close_trade(

                    take_profit,

                    "WIN",

                    candle["timestamp"]
                )


        # ====================================================
        # LIVE EQUITY
        # ====================================================

        self.show_live_equity(
            candle["close"]
        )

        return None


    # ========================================================
    # CLOSE TRADE
    # ========================================================

    def close_trade(
        self,
        exit_price,
        status,
        exit_time
    ):

        trade = self.active_trade

        entry = float(
            trade["entry"]
        )

        exit_price = float(
            exit_price
        )

        quantity = float(
            trade["quantity"]
        )


        # ====================================================
        # CALCULATE PRICE MOVEMENT
        # ====================================================

        if trade["side"] == "BUY":

            price_difference = (
                exit_price - entry
            )

        else:

            price_difference = (
                entry - exit_price
            )


        # ====================================================
        # CALCULATE P&L
        #
        # Project paper model:
        #
        # P&L =
        # price movement × quantity
        # ====================================================

        pnl = (
            price_difference
            * quantity
        )


        # ====================================================
        # UPDATE TRADE
        # ====================================================

        trade["exit_price"] = exit_price

        trade["exit_time"] = exit_time

        trade["status"] = status

        trade["pnl"] = pnl


        # ====================================================
        # UPDATE REALIZED P&L
        # ====================================================

        self.realized_pnl += pnl

        self.trade_number += 1


        # ====================================================
        # FINAL EQUITY
        # ====================================================

        final_equity = (
            self.starting_equity
            + self.realized_pnl
        )


        # ====================================================
        # PRINT RESULT
        # ====================================================

        print()
        print("=" * 60)
        print("PAPER TRADE CLOSED")
        print("=" * 60)

        print(
            "Side        :",
            trade["side"]
        )

        print(
            "Entry       :",
            f"{entry:.2f}"
        )

        print(
            "Exit        :",
            f"{exit_price:.2f}"
        )

        print(
            "Quantity    :",
            f"{quantity:.2f} lots"
        )

        print(
            "Result      :",
            status
        )

        print(
            "P&L         :",
            f"${pnl:+.2f}"
        )

        print(
            "Realized P&L:",
            f"${self.realized_pnl:+.2f}"
        )

        print(
            "Final Equity:",
            f"${final_equity:.2f}"
        )

        print(
            "Entry Time  :",
            trade["entry_time"]
        )

        print(
            "Exit Time   :",
            trade["exit_time"]
        )

        print("=" * 60)


        # ====================================================
        # SAVE COMPLETED TRADE
        # ====================================================

        completed_trade = self.active_trade

        self.save_trade(
            completed_trade
        )


        # ====================================================
        # SAVE EQUITY POINT
        # ====================================================

        self.save_equity_point(

            completed_trade,

            final_equity
        )


        # ====================================================
        # CLEAR ACTIVE TRADE
        # ====================================================

        self.active_trade = None

        return completed_trade


    # ========================================================
    # SAVE TRADE TO CSV
    # ========================================================

    def save_trade(self, trade):

        file_path = (
            "data/trades/paper_trades.csv"
        )

        os.makedirs(
            "data/trades",
            exist_ok=True
        )

        file_exists = os.path.isfile(
            file_path
        )


        with open(
            file_path,
            "a",
            newline=""
        ) as file:

            writer = csv.DictWriter(

                file,

                fieldnames=[

                    "side",

                    "entry",

                    "stop_loss",

                    "take_profit",

                    "risk",

                    "reward",

                    "risk_reward",

                    "quantity",

                    "entry_time",

                    "exit_time",

                    "exit_price",

                    "status",

                    "pnl"
                ]
            )


            if not file_exists:

                writer.writeheader()


            writer.writerow(
                trade
            )


        print()
        print("=" * 60)
        print("TRADE SAVED TO JOURNAL")
        print("=" * 60)

        print(
            "File :",
            file_path
        )

        print("=" * 60)


    # ========================================================
    # SAVE EQUITY CURVE POINT
    # ========================================================

    def save_equity_point(
        self,
        trade,
        equity
    ):

        file_path = (
            "data/trades/equity_curve.csv"
        )

        os.makedirs(
            "data/trades",
            exist_ok=True
        )

        file_exists = os.path.isfile(
            file_path
        )


        with open(
            file_path,
            "a",
            newline=""
        ) as file:

            writer = csv.DictWriter(

                file,

                fieldnames=[

                    "trade_number",

                    "status",

                    "pnl",

                    "equity",

                    "exit_time"
                ]
            )


            if not file_exists:

                writer.writeheader()


            writer.writerow({

                "trade_number":
                    self.trade_number,

                "status":
                    trade["status"],

                "pnl":
                    trade["pnl"],

                "equity":
                    equity,

                "exit_time":
                    trade["exit_time"]
            })


        print()
        print("=" * 60)
        print("EQUITY POINT SAVED")
        print("=" * 60)

        print(
            "Trade Number :",
            self.trade_number
        )

        print(
            "Equity       :",
            f"${equity:.2f}"
        )

        print(
            "File         :",
            file_path
        )

        print("=" * 60)


    # ========================================================
    # GET CURRENT EQUITY
    # ========================================================

    def get_equity(
        self,
        current_price=None
    ):

        unrealized_pnl = 0.0


        if self.active_trade is not None:

            if current_price is not None:

                unrealized_pnl = (
                    self.calculate_unrealized_pnl(
                        current_price
                    )
                )


        return (
            self.starting_equity
            + self.realized_pnl
            + unrealized_pnl
        )


    # ========================================================
    # CHECK ACTIVE STATUS
    # ========================================================

    def is_active(self):

        return (
            self.active_trade is not None
        )