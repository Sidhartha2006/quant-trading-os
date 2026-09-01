import pandas as pd


class M30Builder:

    def __init__(self):
        self.current_m30 = None

    # ============================================================
    # TIMESTAMP CONVERSION
    # ============================================================

    def _convert_timestamp(self, timestamp):

        if isinstance(timestamp, pd.Timestamp):

            if timestamp.tzinfo is None:
                return timestamp.tz_localize("UTC")

            return timestamp.tz_convert("UTC")

        if isinstance(timestamp, (int, float)):

            return pd.to_datetime(
                timestamp,
                unit="ms",
                utc=True
            )

        return pd.to_datetime(
            timestamp,
            utc=True
        )

    # ============================================================
    # PROCESS CANDLE
    # ACCEPTS BOTH:
    #
    # process_candle(candle)
    #
    # OR
    #
    # process_candle(
    #     timestamp,
    #     open,
    #     high,
    #     low,
    #     close,
    #     volume
    # )
    # ============================================================

    def process_candle(
        self,
        timestamp,
        open_price=None,
        high_price=None,
        low_price=None,
        close_price=None,
        volume=None
    ):

        # ========================================================
        # CASE 1: CANDLE DICTIONARY
        # ========================================================

        if isinstance(timestamp, dict):

            candle = timestamp

            timestamp = candle["timestamp"]
            open_price = candle["open"]
            high_price = candle["high"]
            low_price = candle["low"]
            close_price = candle["close"]
            volume = candle["volume"]

        # ========================================================
        # CONVERT VALUES
        # ========================================================

        timestamp = self._convert_timestamp(timestamp)

        open_price = float(open_price)
        high_price = float(high_price)
        low_price = float(low_price)
        close_price = float(close_price)
        volume = float(volume)

        # ========================================================
        # FIND M30 START
        # ========================================================

        minute = (timestamp.minute // 30) * 30

        m30_start = timestamp.replace(
            minute=minute,
            second=0,
            microsecond=0
        )

        # ========================================================
        # FIRST M30 CANDLE
        # ========================================================

        if self.current_m30 is None:

            self.current_m30 = {

                "timestamp": m30_start,

                "open": open_price,

                "high": high_price,

                "low": low_price,

                "close": close_price,

                "volume": volume
            }

            return None

        # ========================================================
        # SAME M30
        # ========================================================

        if m30_start == self.current_m30["timestamp"]:

            self.current_m30["high"] = max(
                self.current_m30["high"],
                high_price
            )

            self.current_m30["low"] = min(
                self.current_m30["low"],
                low_price
            )

            self.current_m30["close"] = close_price

            self.current_m30["volume"] += volume

            return None

        # ========================================================
        # NEW M30 STARTED
        # PREVIOUS M30 IS COMPLETE
        # ========================================================

        completed_m30 = self.current_m30.copy()

        # ========================================================
        # START NEW M30
        # ========================================================

        self.current_m30 = {

            "timestamp": m30_start,

            "open": open_price,

            "high": high_price,

            "low": low_price,

            "close": close_price,

            "volume": volume
        }

        # ========================================================
        # PRINT COMPLETED M30
        # ========================================================

        print()
        print("=" * 60)
        print("COMPLETED M30 CANDLE")
        print("=" * 60)

        print(
            f"Time   : {completed_m30['timestamp']}"
        )

        print(
            f"Open   : {completed_m30['open']:.2f}"
        )

        print(
            f"High   : {completed_m30['high']:.2f}"
        )

        print(
            f"Low    : {completed_m30['low']:.2f}"
        )

        print(
            f"Close  : {completed_m30['close']:.2f}"
        )

        print(
            f"Volume : {completed_m30['volume']:.2f}"
        )

        print("=" * 60)

        return completed_m30

    # ============================================================
    # COMPATIBILITY METHOD
    # ============================================================

    def process_1m_candle(
        self,
        timestamp,
        open_price,
        high_price,
        low_price,
        close_price,
        volume
    ):

        return self.process_candle(
            timestamp,
            open_price,
            high_price,
            low_price,
            close_price,
            volume
        )

    # ============================================================
    # DICTIONARY COMPATIBILITY METHOD
    # ============================================================

    def add_candle(self, candle):

        return self.process_candle(candle)