import json
import websocket
from m30_builder import M30Builder

SYMBOL = "xauusdt"
INTERVAL = "1m"

URL = f"wss://fstream.binance.com/ws/{SYMBOL}@kline_{INTERVAL}"

m30_builder = M30Builder()


def on_open(ws):
    print("=" * 60)
    print("BINANCE FUTURES XAUUSDT LIVE DATA")
    print("=" * 60)
    print("Connected!")
    print("WebSocket URL:", URL)
    print("Waiting for closed 1-minute candles...")
    print()


def on_message(ws, message):

    try:

        data = json.loads(message)

        if "k" not in data:
            return

        kline = data["k"]

        # We only process COMPLETED 1-minute candles.
        if not kline["x"]:
            return

        timestamp = kline["t"]

        open_price = float(kline["o"])
        high_price = float(kline["h"])
        low_price = float(kline["l"])
        close_price = float(kline["c"])
        volume = float(kline["v"])

        print(
            f"M1 CLOSED | "
            f"O:{open_price:.2f} "
            f"H:{high_price:.2f} "
            f"L:{low_price:.2f} "
            f"C:{close_price:.2f}"
        )

        # Send completed M1 candle to M30 builder.
        completed_m30 = m30_builder.process_1m_candle(
            timestamp=timestamp,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume
        )

        # A completed M30 candle is returned
        # every 30 completed M1 candles.
        if completed_m30 is not None:

            print()
            print(">>> M30 CANDLE READY")
            print(
                f"M30 Open : {completed_m30['open']:.2f}"
            )
            print(
                f"M30 High : {completed_m30['high']:.2f}"
            )
            print(
                f"M30 Low  : {completed_m30['low']:.2f}"
            )
            print(
                f"M30 Close: {completed_m30['close']:.2f}"
            )
            print()


    except Exception as e:

        print()
        print("Message processing error:")
        print(type(e).__name__, e)


def on_error(ws, error):

    print()
    print("=" * 60)
    print("WEBSOCKET ERROR")
    print("=" * 60)
    print(error)


def on_close(ws, close_status_code, close_msg):

    print()
    print("=" * 60)
    print("WEBSOCKET CLOSED")
    print("=" * 60)
    print("Status code:", close_status_code)
    print("Message:", close_msg)


def main():

    print("Connecting to Binance...")
    print(URL)

    ws = websocket.WebSocketApp(
        URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    try:

        ws.run_forever()

    except KeyboardInterrupt:

        print()
        print("Bot stopped by user.")

        ws.close()


if __name__ == "__main__":
    main()