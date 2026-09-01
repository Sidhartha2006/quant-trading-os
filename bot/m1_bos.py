class M1BOS:

    def __init__(self):

        self.candles = []

        self.active_direction = None

        self.last_bos = None

        # --------------------------------------------
        # MARKET STRUCTURE
        # --------------------------------------------

        self.last_high = None
        self.last_low = None

        self.last_high_type = None
        self.last_low_type = None

        # --------------------------------------------
        # STRUCTURE LEVELS WE WANT TO BREAK
        # --------------------------------------------

        self.higher_low = None
        self.lower_high = None

        # --------------------------------------------
        # SETTINGS
        # --------------------------------------------

        self.max_candles = 100

        # Minimum percentage of candle range
        # that must be body.
        #
        # Example:
        # 0.60 = body must be at least 60%
        # of total candle range.
        #
        self.strong_body_ratio = 0.60

    # ========================================================
    # ACTIVATE BOS WATCH
    # ========================================================

    def set_breakout(self, direction):

        self.active_direction = direction

        self.candles = []

        self.last_bos = None

        self.last_high = None
        self.last_low = None

        self.last_high_type = None
        self.last_low_type = None

        self.higher_low = None
        self.lower_high = None

        print()
        print("=" * 60)
        print("M1 MARKET STRUCTURE WATCH ACTIVATED")
        print("=" * 60)

        print(
            f"M30 Direction : {direction}"
        )

        print()
        print(
            "Monitoring M1 structure:"
        )

        print(
            "HH → HL → HH"
        )

        print(
            "LL → LH → LL"
        )

        print()
        print(
            "Waiting for strong break of HL/LH..."
        )

        print("=" * 60)

    # ========================================================
    # STRONG CANDLE
    # ========================================================

    def is_strong_candle(self, candle, direction):

        open_price = float(candle["open"])
        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])

        candle_range = high - low

        if candle_range <= 0:
            return False

        body = abs(close - open_price)

        body_ratio = body / candle_range

        # --------------------------------------------
        # BULLISH STRONG CANDLE
        # --------------------------------------------

        if direction == "BULLISH":

            bullish = close > open_price

            strong_body = (
                body_ratio >= self.strong_body_ratio
            )

            close_near_high = (
                (high - close) / candle_range <= 0.25
            )

            return (
                bullish
                and
                strong_body
                and
                close_near_high
            )

        # --------------------------------------------
        # BEARISH STRONG CANDLE
        # --------------------------------------------

        if direction == "BEARISH":

            bearish = close < open_price

            strong_body = (
                body_ratio >= self.strong_body_ratio
            )

            close_near_low = (
                (close - low) / candle_range <= 0.25
            )

            return (
                bearish
                and
                strong_body
                and
                close_near_low
            )

        return False

    # ========================================================
    # PROCESS M1 CANDLE
    # ========================================================

    def process_candle(self, candle):

        if self.active_direction is None:
            return None

        self.candles.append(candle)

        if len(self.candles) > self.max_candles:

            self.candles.pop(0)

        # Need at least two candles
        if len(self.candles) < 2:
            return None

        current = self.candles[-1]

        previous = self.candles[-2]

        current_high = float(
            current["high"]
        )

        current_low = float(
            current["low"]
        )

        current_close = float(
            current["close"]
        )

        previous_high = float(
            previous["high"]
        )

        previous_low = float(
            previous["low"]
        )

        # ====================================================
        # BUILD MARKET STRUCTURE
        # ====================================================

        # ----------------------------------------------------
        # FIRST CANDLE
        # ----------------------------------------------------

        if self.last_high is None:

            self.last_high = previous_high

        if self.last_low is None:

            self.last_low = previous_low

        # ====================================================
        # HIGHER HIGH
        # ====================================================

        if current_high > self.last_high:

            self.last_high = current_high

            self.last_high_type = "HH"

            print(
                f"M1 STRUCTURE → HH : "
                f"{current_high:.2f}"
            )

        # ====================================================
        # LOWER HIGH
        # ====================================================

        elif current_high < self.last_high:

            self.last_high_type = "LH"

            self.lower_high = current_high

            print(
                f"M1 STRUCTURE → LH : "
                f"{current_high:.2f}"
            )

        # ====================================================
        # LOWER LOW
        # ====================================================

        if current_low < self.last_low:

            self.last_low = current_low

            self.last_low_type = "LL"

            print(
                f"M1 STRUCTURE → LL : "
                f"{current_low:.2f}"
            )

        # ====================================================
        # HIGHER LOW
        # ====================================================

        elif current_low > self.last_low:

            self.last_low_type = "HL"

            self.higher_low = current_low

            print(
                f"M1 STRUCTURE → HL : "
                f"{current_low:.2f}"
            )

        # ====================================================
        # BEARISH MARKET STRUCTURE SHIFT
        #
        # Price breaks the latest HIGHER LOW
        # with a strong bearish candle.
        # ====================================================

        if self.higher_low is not None:

            if current_close < self.higher_low:

                strong_bearish = (
                    self.is_strong_candle(
                        current,
                        "BEARISH"
                    )
                )

                if strong_bearish:

                    bos = {

                        "direction":
                            "BEARISH_BOS",

                        "bos_price":
                            current_close,

                        "structure_level":
                            self.higher_low,

                        "structure_type":
                            "HL_BROKEN",

                        "timestamp":
                            current["timestamp"]
                    }

                    self.last_bos = bos

                    self.active_direction = None

                    print()
                    print("=" * 60)
                    print(
                        "🔴 BEARISH MARKET STRUCTURE SHIFT"
                    )
                    print("=" * 60)

                    print(
                        f"Broken Structure : "
                        f"Higher Low"
                    )

                    print(
                        f"HL Level         : "
                        f"{self.higher_low:.2f}"
                    )

                    print(
                        f"Break Candle     : "
                        f"{current_close:.2f}"
                    )

                    print(
                        f"Time             : "
                        f"{current['timestamp']}"
                    )

                    print()
                    print(
                        "M1 TREND → BEARISH"
                    )

                    print(
                        "NEXT STEP → WAIT FOR "
                        "M1 RETEST"
                    )

                    print("=" * 60)

                    return bos

        # ====================================================
        # BULLISH MARKET STRUCTURE SHIFT
        #
        # Price breaks the latest LOWER HIGH
        # with a strong bullish candle.
        # ====================================================

        if self.lower_high is not None:

            if current_close > self.lower_high:

                strong_bullish = (
                    self.is_strong_candle(
                        current,
                        "BULLISH"
                    )
                )

                if strong_bullish:

                    bos = {

                        "direction":
                            "BULLISH_BOS",

                        "bos_price":
                            current_close,

                        "structure_level":
                            self.lower_high,

                        "structure_type":
                            "LH_BROKEN",

                        "timestamp":
                            current["timestamp"]
                    }

                    self.last_bos = bos

                    self.active_direction = None

                    print()
                    print("=" * 60)
                    print(
                        "🟢 BULLISH MARKET STRUCTURE SHIFT"
                    )
                    print("=" * 60)

                    print(
                        f"Broken Structure : "
                        f"Lower High"
                    )

                    print(
                        f"LH Level        : "
                        f"{self.lower_high:.2f}"
                    )

                    print(
                        f"Break Candle    : "
                        f"{current_close:.2f}"
                    )

                    print(
                        f"Time            : "
                        f"{current['timestamp']}"
                    )

                    print()
                    print(
                        "M1 TREND → BULLISH"
                    )

                    print(
                        "NEXT STEP → WAIT FOR "
                        "M1 RETEST"
                    )

                    print("=" * 60)

                    return bos

        return None

    # ========================================================
    # GET LAST BOS
    # ========================================================

    def get_last_bos(self):

        return self.last_bos