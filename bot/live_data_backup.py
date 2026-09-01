import json
import time
import websocket

SYMBOL = "xauusdt"
INTERVAL = "1m"

URL = f"wss://fstream.binance.com/ws/{SYMBOL}@kline_{INTERVAL}"


def on_open(ws):
    print("=" * 60)
    print("BINANCE FUTURES XAUUSDT LIVE DATA")
    print("=" * 60)
    print("Connected!")
    print("WebSocket URL:", URL)
    print("Waiting for candles...")
    print()


def on_message(ws, message):
    try:
        data = json.loads(message)

        if "k" not in data:
            return

        kline = data["k"]

        symbol = kline["s"]
        interval = kline["i"]

        open_price = float(kline["o"])
        high_price = float(kline["h"])
        low_price = float(kline["l"])
        close_price = float(kline["c"])

        candle_closed = kline["x"]

        print(
            f"{symbol} | {interval} | "
            f"O:{open_price:.2f} "
            f"H:{high_price:.2f} "
            f"L:{low_price:.2f} "
            f"C:{close_price:.2f} | "
            f"Closed: {candle_closed}"
        )

    except Exception as e:
        print("Message processing error:", e)


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

        try:
            ws.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()