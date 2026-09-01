import pandas as pd


class M30Liquidity:

    def __init__(self, left_bars=3, right_bars=3):

        self.left_bars = left_bars
        self.right_bars = right_bars

        self.candles = []

        self.high_liquidity = None
        self.low_liquidity = None

    def process_m30_candle(self, candle):

        self.candles.append(candle)

        # We need enough candles to confirm a swing.
        required = self.left_bars + self.right_bars + 1

        if len(self.candles) < required:
            return None

        # The candle in the middle is the candle
        # whose swing status we can now confirm.
        index = len(self.candles) - self.right_bars - 1

        current = self.candles[index]

        left = self.candles[
            index - self.left_bars:index
        ]

        right = self.candles[
            index + 1:index + 1 + self.right_bars
        ]

        current_high = current["high"]
        current_low = current["low"]

        is_swing_high = (
            all(current_high > c["high"] for c in left)
            and
            all(current_high > c["high"] for c in right)
        )

        is_swing_low = (
            all(current_low < c["low"] for c in left)
            and
            all(current_low < c["low"] for c in right)
        )

        update = None

        if is_swing_high:

            self.high_liquidity = current_high

            update = {
                "type": "HIGH_LIQUIDITY",
                "price": current_high,
                "time": current["timestamp"]
            }

            print()
            print("=" * 60)
            print("M30 HIGH LIQUIDITY DETECTED")
            print("=" * 60)
            print(
                f"Time  : {current['timestamp']}"
            )
            print(
                f"Price : {current_high:.2f}"
            )
            print("=" * 60)

        if is_swing_low:

            self.low_liquidity = current_low

            update = {
                "type": "LOW_LIQUIDITY",
                "price": current_low,
                "time": current["timestamp"]
            }

            print()
            print("=" * 60)
            print("M30 LOW LIQUIDITY DETECTED")
            print("=" * 60)
            print(
                f"Time  : {current['timestamp']}"
            )
            print(
                f"Price : {current_low:.2f}"
            )
            print("=" * 60)

        return update

    def get_levels(self):

        return {
            "high_liquidity": self.high_liquidity,
            "low_liquidity": self.low_liquidity
        }