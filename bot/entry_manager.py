class EntryManager:

    def __init__(
        self,
        stop_buffer=0.50,
        risk_reward=2.0
    ):

        self.stop_buffer = stop_buffer

        self.risk_reward = risk_reward

        self.active_retest = None

        self.previous_candle = None

        self.last_entry = None

    # ========================================================
    # SET RETEST
    # ========================================================

    def set_retest(self, retest):

        self.active_retest = retest

        self.previous_candle = None

        print()
        print("=" * 60)
        print("ENTRY CONFIRMATION WATCH ACTIVATED")
        print("=" * 60)

        print(
            f"Direction : "
            f"{retest['direction']}"
        )

        print(
            f"BOS Price : "
            f"{retest['bos_price']:.2f}"
        )

        print(
            "Waiting for confirmation candle..."
        )

        print("=" * 60)

    # ========================================================
    # PROCESS M1 CANDLE
    # ========================================================

    def process_candle(self, candle):

        if self.active_retest is None:

            return None

        current = candle

        # ====================================================
        # FIRST CANDLE AFTER RETEST
        # ====================================================

        if self.previous_candle is None:

            self.previous_candle = current

            return None

        previous = self.previous_candle

        direction = self.active_retest["direction"]

        # ====================================================
        # BULLISH ENTRY
        #
        # Current candle must:
        #
        # 1. Close above previous candle high
        # 2. Be bullish
        #
        # SL = current candle low - buffer
        # ====================================================

        if direction == "BULLISH_RETEST":

            bullish_candle = (
                current["close"] > current["open"]
            )

            breaks_previous_high = (
                current["close"] > previous["high"]
            )

            if (
                bullish_candle
                and
                breaks_previous_high
            ):

                entry = float(
                    current["close"]
                )

                stop_loss = (
                    float(current["low"])
                    - self.stop_buffer
                )

                risk = entry - stop_loss

                if risk <= 0:

                    self.previous_candle = current

                    return None

                reward = (
                    risk * self.risk_reward
                )

                take_profit = (
                    entry + reward
                )

                trade = {

                    "side": "BUY",

                    "entry": entry,

                    "stop_loss": stop_loss,

                    "take_profit": take_profit,

                    "risk": risk,

                    "reward": reward,

                    "risk_reward":
                        self.risk_reward,

                    "timestamp":
                        current["timestamp"]
                }

                self.last_entry = trade

                self.active_retest = None

                self.previous_candle = None

                self._print_trade(trade)

                return trade

        # ====================================================
        # BEARISH ENTRY
        #
        # Current candle must:
        #
        # 1. Close below previous candle low
        # 2. Be bearish
        #
        # SL = current candle high + buffer
        # ====================================================

        if direction == "BEARISH_RETEST":

            bearish_candle = (
                current["close"] < current["open"]
            )

            breaks_previous_low = (
                current["close"] < previous["low"]
            )

            if (
                bearish_candle
                and
                breaks_previous_low
            ):

                entry = float(
                    current["close"]
                )

                stop_loss = (
                    float(current["high"])
                    + self.stop_buffer
                )

                risk = stop_loss - entry

                if risk <= 0:

                    self.previous_candle = current

                    return None

                reward = (
                    risk * self.risk_reward
                )

                take_profit = (
                    entry - reward
                )

                trade = {

                    "side": "SELL",

                    "entry": entry,

                    "stop_loss": stop_loss,

                    "take_profit": take_profit,

                    "risk": risk,

                    "reward": reward,

                    "risk_reward":
                        self.risk_reward,

                    "timestamp":
                        current["timestamp"]
                }

                self.last_entry = trade

                self.active_retest = None

                self.previous_candle = None

                self._print_trade(trade)

                return trade

        # Move current candle forward

        self.previous_candle = current

        return None

    # ========================================================
    # PRINT TRADE
    # ========================================================

    def _print_trade(self, trade):

        print()
        print("=" * 60)
        print("🚨 ENTRY SIGNAL CREATED")
        print("=" * 60)

        print(
            f"Side        : "
            f"{trade['side']}"
        )

        print(
            f"Entry       : "
            f"{trade['entry']:.2f}"
        )

        print(
            f"Stop Loss   : "
            f"{trade['stop_loss']:.2f}"
        )

        print(
            f"Take Profit : "
            f"{trade['take_profit']:.2f}"
        )

        print(
            f"Risk        : "
            f"{trade['risk']:.2f}"
        )

        print(
            f"Reward      : "
            f"{trade['reward']:.2f}"
        )

        print(
            f"Risk/Reward : "
            f"1:{trade['risk_reward']:.2f}"
        )

        print(
            f"Timestamp   : "
            f"{trade['timestamp']}"
        )

        print("=" * 60)

    # ========================================================
    # LAST ENTRY
    # ========================================================

    def get_last_entry(self):

        return self.last_entry