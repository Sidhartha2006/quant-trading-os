
class M1Retest:

    def __init__(self, tolerance=0.50):

        self.active_bos = None

        self.retest_detected = False

        self.tolerance = tolerance

    # ========================================================
    # SET BOS
    # ========================================================

    def set_bos(self, bos):

        self.active_bos = bos

        self.retest_detected = False

        print()
        print("=" * 60)
        print("M1 RETEST WATCH ACTIVATED")
        print("=" * 60)

        print(
            f"Direction : {bos['direction']}"
        )

        print(
            f"BOS Price : {bos['bos_price']:.2f}"
        )

        print(
            f"Structure : {bos['structure_level']:.2f}"
        )

        print(
            "Waiting for price to retest BOS level..."
        )

        print("=" * 60)

    # ========================================================
    # PROCESS M1 CANDLE
    # ========================================================

    def process_candle(self, candle):

        if self.active_bos is None:
            return None

        if self.retest_detected:
            return None

        direction = self.active_bos["direction"]

        bos_price = float(
            self.active_bos["bos_price"]
        )

        high = float(candle["high"])

        low = float(candle["low"])

        close = float(candle["close"])

        timestamp = candle["timestamp"]

        # ====================================================
        # BULLISH RETEST
        # ====================================================

        if direction == "BULLISH_BOS":

            # Price must come back to BOS level.
            #
            # Candle low should reach BOS price
            # within allowed tolerance.

            distance = abs(
                low - bos_price
            )

            touched_bos = (
                low <= bos_price
                or
                distance <= self.tolerance
            )

            # Candle must close back ABOVE BOS.
            valid_close = (
                close > bos_price
            )

            if touched_bos and valid_close:

                retest = {

                    "direction":
                        "BULLISH_RETEST",

                    "retest_price":
                        close,

                    "bos_price":
                        bos_price,

                    "candle_high":
                        high,

                    "candle_low":
                        low,

                    "candle_open":
                        float(candle["open"]),

                    "candle_close":
                        close,

                    "timestamp":
                        timestamp
                }

                self.retest_detected = True

                print()
                print("=" * 60)
                print("🟢 M1 BULLISH RETEST CONFIRMED")
                print("=" * 60)

                print(
                    f"BOS Price : {bos_price:.2f}"
                )

                print(
                    f"Retest Low: {low:.2f}"
                )

                print(
                    f"Close     : {close:.2f}"
                )

                print(
                    f"Time      : {timestamp}"
                )

                print()
                print(
                    "NEXT STEP → WAIT FOR "
                    "BULLISH CONFIRMATION CANDLE"
                )

                print("=" * 60)

                return retest

        # ====================================================
        # BEARISH RETEST
        # ====================================================

        if direction == "BEARISH_BOS":

            # Price must come back to BOS level.

            distance = abs(
                high - bos_price
            )

            touched_bos = (
                high >= bos_price
                or
                distance <= self.tolerance
            )

            # Candle must close back BELOW BOS.

            valid_close = (
                close < bos_price
            )

            if touched_bos and valid_close:

                retest = {

                    "direction":
                        "BEARISH_RETEST",

                    "retest_price":
                        close,

                    "bos_price":
                        bos_price,

                    "candle_high":
                        high,

                    "candle_low":
                        low,

                    "candle_open":
                        float(candle["open"]),

                    "candle_close":
                        close,

                    "timestamp":
                        timestamp
                }

                self.retest_detected = True

                print()
                print("=" * 60)
                print("🔴 M1 BEARISH RETEST CONFIRMED")
                print("=" * 60)

                print(
                    f"BOS Price  : {bos_price:.2f}"
                )

                print(
                    f"Retest High: {high:.2f}"
                )

                print(
                    f"Close      : {close:.2f}"
                )

                print(
                    f"Time       : {timestamp}"
                )

                print()
                print(
                    "NEXT STEP → WAIT FOR "
                    "BEARISH CONFIRMATION CANDLE"
                )

                print("=" * 60)

                return retest

        return None

    # ========================================================
    # RESET
    # ========================================================

    def reset(self):

        self.active_bos = None

        self.retest_detected = False

