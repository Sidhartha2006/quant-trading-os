class EntryEngine:

    def __init__(
        self,
        risk_reward=2.0,
        stop_buffer=0.50
    ):

        self.risk_reward = risk_reward
        self.stop_buffer = stop_buffer

        self.last_trade = None

    # ========================================================
    # CREATE TRADE
    # ========================================================

    def create_trade(self, retest):

        direction = retest["direction"]

        entry_price = float(
            retest["retest_price"]
        )

        bos_price = float(
            retest["bos_price"]
        )

        # ====================================================
        # BULLISH TRADE
        # ====================================================

        if direction == "BULLISH_RETEST":

            stop_loss = (
                bos_price -
                self.stop_buffer
            )

            risk = (
                entry_price -
                stop_loss
            )

            if risk <= 0:
                return None

            take_profit = (
                entry_price +
                risk * self.risk_reward
            )

            trade = {

                "side": "BUY",

                "entry": entry_price,

                "stop_loss": stop_loss,

                "take_profit": take_profit,

                "risk": risk,

                "reward": (
                    take_profit -
                    entry_price
                ),

                "risk_reward": self.risk_reward,

                "timestamp": retest["timestamp"]
            }

        # ====================================================
        # BEARISH TRADE
        # ====================================================

        elif direction == "BEARISH_RETEST":

            stop_loss = (
                bos_price +
                self.stop_buffer
            )

            risk = (
                stop_loss -
                entry_price
            )

            if risk <= 0:
                return None

            take_profit = (
                entry_price -
                risk * self.risk_reward
            )

            trade = {

                "side": "SELL",

                "entry": entry_price,

                "stop_loss": stop_loss,

                "take_profit": take_profit,

                "risk": risk,

                "reward": (
                    entry_price -
                    take_profit
                ),

                "risk_reward": self.risk_reward,

                "timestamp": retest["timestamp"]
            }

        else:

            return None

        self.last_trade = trade

        return trade

    # ========================================================
    # PRINT TRADE
    # ========================================================

    def print_trade(self, trade):

        print()
        print("=" * 60)
        print("PAPER TRADE CREATED")
        print("=" * 60)

        print(
            "Side        :",
            trade["side"]
        )

        print(
            "Entry       :",
            f"{trade['entry']:.2f}"
        )

        print(
            "Stop Loss   :",
            f"{trade['stop_loss']:.2f}"
        )

        print(
            "Take Profit :",
            f"{trade['take_profit']:.2f}"
        )

        print(
            "Risk        :",
            f"{trade['risk']:.2f}"
        )

        print(
            "Reward      :",
            f"{trade['reward']:.2f}"
        )

        print(
            "Risk/Reward :",
            f"1:{trade['risk_reward']:.2f}"
        )

        print(
            "Timestamp   :",
            trade["timestamp"]
        )

        print("=" * 60)
        