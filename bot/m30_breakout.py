class M30Breakout:

    def __init__(self):

        self.last_breakout = None

    # ========================================================
    # CHECK M30 BREAKOUT
    # ========================================================

    def check_breakout(self, candle, liquidity_levels):

        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])

        high_liquidity = liquidity_levels.get(
            "high_liquidity"
        )

        low_liquidity = liquidity_levels.get(
            "low_liquidity"
        )

        # ====================================================
        # BULLISH M30 BREAKOUT
        # Price closes ABOVE previous high liquidity
        # ====================================================

        if (
            high_liquidity is not None
            and close > high_liquidity
        ):

            breakout = {

                "direction": "BULLISH_BREAKOUT",

                "price": close,

                "liquidity_price": high_liquidity,

                "timestamp": candle["timestamp"]
            }

            self.last_breakout = breakout

            print()
            print("=" * 60)
            print("🟢 M30 BULLISH BREAKOUT")
            print("=" * 60)

            print(
                f"Time      : {candle['timestamp']}"
            )

            print(
                f"Liquidity : {high_liquidity:.2f}"
            )

            print(
                f"M30 High  : {high:.2f}"
            )

            print(
                f"M30 Close : {close:.2f}"
            )

            print(
                f"Break     : {close - high_liquidity:.2f}"
            )

            print("=" * 60)

            return breakout

        # ====================================================
        # BEARISH M30 BREAKOUT
        # Price closes BELOW previous low liquidity
        # ====================================================

        if (
            low_liquidity is not None
            and close < low_liquidity
        ):

            breakout = {

                "direction": "BEARISH_BREAKOUT",

                "price": close,

                "liquidity_price": low_liquidity,

                "timestamp": candle["timestamp"]
            }

            self.last_breakout = breakout

            print()
            print("=" * 60)
            print("🔴 M30 BEARISH BREAKOUT")
            print("=" * 60)

            print(
                f"Time      : {candle['timestamp']}"
            )

            print(
                f"Liquidity : {low_liquidity:.2f}"
            )

            print(
                f"M30 Low   : {low:.2f}"
            )

            print(
                f"M30 Close : {close:.2f}"
            )

            print(
                f"Break     : {low_liquidity - close:.2f}"
            )

            print("=" * 60)

            return breakout

        return None