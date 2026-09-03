import time
import requests
import os

from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

from m30_builder import M30Builder
from m30_liquidity import M30Liquidity
from m30_breakout import M30Breakout
from m1_bos import M1BOS
from m1_retest import M1Retest
from entry_manager import EntryManager
from paper_trade import PaperTrade
from equity_monitor import EquityMonitor
from risk_manager import RiskManager


# ============================================================
# CONFIG
# ============================================================

SYMBOL = os.getenv("SYMBOL", "XAUUSDT")

INTERVAL = "1m"

BASE_URL = (
    "https://fapi.binance.com/fapi/v1/klines"
)

RISK_REWARD = 2.0

STOP_BUFFER = 0.50

PAPER_TRADING = os.getenv("PAPER_TRADING", "True").lower() == "true"

REAL_ORDERS = os.getenv("REAL_ORDERS", "False").lower() == "true"

STARTING_BALANCE = float(os.getenv("STARTING_BALANCE", "10000"))


# ============================================================
# V1 RISK RULES
# ============================================================

RISK_PERCENT = float(os.getenv("RISK_PERCENT", "0.5"))

MAX_LOTS = 0.5

MAX_OPEN_POSITIONS = 1


# ============================================================
# BINANCE DATA
# ============================================================

def get_latest_candle():

    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "limit": 2
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    # Last completed M1 candle
    candle = data[-2]

    return {
        "timestamp":
            datetime.fromtimestamp(
                candle[0] / 1000,
                tz=timezone.utc
            ),

        "open": float(candle[1]),

        "high": float(candle[2]),

        "low": float(candle[3]),

        "close": float(candle[4]),

        "volume": float(candle[5])
    }


# ============================================================
# HISTORICAL M30 DATA
# ============================================================

def load_historical_m30():

    print()
    print("=" * 60)
    print("LOADING HISTORICAL M30 DATA")
    print("=" * 60)

    params = {
        "symbol": SYMBOL,
        "interval": "30m",
        "limit": 100
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    candles = []

    # Ignore currently forming M30 candle

    for c in data[:-1]:

        candles.append({

            "timestamp":
                datetime.fromtimestamp(
                    c[0] / 1000,
                    tz=timezone.utc
                ),

            "open": float(c[1]),

            "high": float(c[2]),

            "low": float(c[3]),

            "close": float(c[4]),

            "volume": float(c[5])
        })

    print(
        f"Historical M30 candles loaded: "
        f"{len(candles)}"
    )

    return candles


# ============================================================
# COMPONENTS
# ============================================================

m30_builder = M30Builder()

m30_liquidity = M30Liquidity(
    left_bars=3,
    right_bars=3
)

m30_breakout = M30Breakout()

m1_bos = M1BOS()

m1_retest = M1Retest(
    tolerance=0.50
)

entry_manager = EntryManager(
    stop_buffer=STOP_BUFFER,
    risk_reward=RISK_REWARD
)

paper_trade = PaperTrade()

equity_monitor = EquityMonitor(
    starting_balance=STARTING_BALANCE
)

risk_manager = RiskManager(
    risk_percent=RISK_PERCENT,
    max_lots=MAX_LOTS,
    max_open_positions=MAX_OPEN_POSITIONS
)


# ============================================================
# BUILD HISTORICAL M30 LIQUIDITY
# ============================================================

print()
print("Building historical M30 liquidity...")
print()

historical_m30 = load_historical_m30()

for candle in historical_m30:

    m30_liquidity.process_m30_candle(
        candle
    )


levels = m30_liquidity.get_levels()


print()
print("=" * 60)
print("INITIAL M30 LIQUIDITY")
print("=" * 60)

print(
    f"High Liquidity : "
    f"{levels['high_liquidity']}"
)

print(
    f"Low Liquidity  : "
    f"{levels['low_liquidity']}"
)

print("=" * 60)


# ============================================================
# STATE
# ============================================================

last_m1_timestamp = None

active_setup = None

bos_detected = False

retest_detected = False

entry_taken = False


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 60)
print("BINANCE FUTURES XAUUSDT LIVE STRATEGY")
print("=" * 60)

print(
    "Data source : Binance Futures REST"
)

print(
    "Symbol      :", SYMBOL
)

print(
    "Timeframe   :", INTERVAL
)

print()
print("STRATEGY PIPELINE")
print("----------------------------------------")

print("M30 Previous Liquidity")
print("        ↓")
print("M30 Breakout")
print("        ↓")
print("M1 BOS")
print("        ↓")
print("M1 Retest of BOS")
print("        ↓")
print("M1 Confirmation Candle")
print("        ↓")
print("ENTRY")
print("        ↓")
print("RISK MANAGER")
print("        ↓")
print("SL + Buffer / TP 1:2")
print("        ↓")
print("Paper Trade")
print("        ↓")
print("Live Equity")
print("----------------------------------------")

print(
    f"Risk/Reward     : 1:{RISK_REWARD}"
)

print(
    f"Stop Buffer     : {STOP_BUFFER}"
)

print(
    f"Risk Limit      : {RISK_PERCENT}%"
)

print(
    f"Maximum Lots    : {MAX_LOTS}"
)

print(
    f"Max Open Trades : {MAX_OPEN_POSITIONS}"
)

print(
    f"Starting Equity : ${STARTING_BALANCE:.2f}"
)

print()
print("Real Binance orders: DISABLED")
print("Paper trading: ENABLED")

print()
print("Starting strategy engine...")
print()


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    try:

        # ====================================================
        # GET LATEST CLOSED M1
        # ====================================================

        candle = get_latest_candle()

        timestamp = candle["timestamp"]


        # ====================================================
        # DUPLICATE PROTECTION
        # ====================================================

        if (
            last_m1_timestamp is not None
            and
            timestamp <= last_m1_timestamp
        ):

            time.sleep(2)

            continue


        last_m1_timestamp = timestamp


        # ====================================================
        # PRINT M1
        # ====================================================

        print(
            f"M1 CLOSED | "
            f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC | "
            f"O:{candle['open']:.2f} "
            f"H:{candle['high']:.2f} "
            f"L:{candle['low']:.2f} "
            f"C:{candle['close']:.2f}"
        )


        # ====================================================
        # CHECK ACTIVE PAPER TRADE
        # ====================================================

        if PAPER_TRADING and paper_trade.is_active():

            result = paper_trade.check_trade(
                candle
            )


            # =================================================
            # TRADE CLOSED
            # =================================================

            if result is not None:

                print()
                print("=" * 60)
                print("PAPER TRADE RESULT")
                print("=" * 60)

                print(
                    f"Status : "
                    f"{result['status']}"
                )

                print(
                    f"P&L    : "
                    f"{result['pnl']:.2f}"
                )

                print("=" * 60)


                # =============================================
                # UPDATE REALIZED EQUITY
                # =============================================

                equity_monitor.update_realized_pnl(
                    result["pnl"]
                )


                # =============================================
                # RESET SETUP
                # =============================================

                active_setup = None

                bos_detected = False

                retest_detected = False

                entry_taken = False


            # =================================================
            # TRADE STILL ACTIVE
            # =================================================

            else:

                active_trade = (
                    paper_trade.active_trade
                )


                # =============================================
                # UPDATE FLOATING P&L
                # =============================================

                equity_monitor.update_floating_pnl(

                    active_trade["side"],

                    active_trade["entry"],

                    candle["close"]
                )


        # ====================================================
        # M30 BUILDER
        # ====================================================

        completed_m30 = (
            m30_builder.process_candle(
                candle
            )
        )


        # ====================================================
        # NEW M30 COMPLETED
        # ====================================================

        if completed_m30 is not None:

            print()
            print("=" * 60)
            print(">>> NEW M30 CANDLE COMPLETED")
            print("=" * 60)

            print(
                f"Time  : "
                f"{completed_m30['timestamp']}"
            )

            print(
                f"Open  : "
                f"{completed_m30['open']:.2f}"
            )

            print(
                f"High  : "
                f"{completed_m30['high']:.2f}"
            )

            print(
                f"Low   : "
                f"{completed_m30['low']:.2f}"
            )

            print(
                f"Close : "
                f"{completed_m30['close']:.2f}"
            )

            print("=" * 60)


            # =================================================
            # UPDATE LIQUIDITY
            # =================================================

            m30_liquidity.process_m30_candle(
                completed_m30
            )

            levels = (
                m30_liquidity.get_levels()
            )


            print()
            print("CURRENT M30 LIQUIDITY")
            print("----------------------------------------")

            print(
                f"High Liquidity : "
                f"{levels['high_liquidity']}"
            )

            print(
                f"Low Liquidity  : "
                f"{levels['low_liquidity']}"
            )

            print("----------------------------------------")


            # =================================================
            # CHECK M30 BREAKOUT
            # =================================================

            if not paper_trade.is_active():

                breakout = (
                    m30_breakout.check_breakout(
                        completed_m30,
                        levels
                    )
                )

            else:

                breakout = None


            # =================================================
            # BREAKOUT FOUND
            # =================================================

            if breakout is not None:

                active_setup = breakout

                bos_detected = False

                retest_detected = False

                entry_taken = False

                direction = (
                    breakout["direction"]
                )


                print()
                print("=" * 60)
                print("🔥 M30 BREAKOUT CONFIRMED")
                print("=" * 60)

                print(
                    f"Direction : {direction}"
                )

                print(
                    f"Breakout  : "
                    f"{breakout['price']:.2f}"
                )

                print(
                    f"Liquidity : "
                    f"{breakout['liquidity_price']:.2f}"
                )

                print(
                    f"Time      : "
                    f"{breakout['timestamp']}"
                )

                print("=" * 60)


                # =============================================
                # ACTIVATE M1 BOS
                # =============================================

                m1_bos.set_breakout(
                    direction
                )


        # ====================================================
        # M1 BOS
        # ====================================================

        if (
            active_setup is not None
            and
            not bos_detected
            and
            not paper_trade.is_active()
        ):

            bos = (
                m1_bos.process_candle(
                    candle
                )
            )


            if bos is not None:

                bos_detected = True


                print()
                print("=" * 60)
                print("✅ M1 BOS CONFIRMED")
                print("=" * 60)

                print(
                    f"Direction : "
                    f"{bos['direction']}"
                )

                print(
                    f"BOS Price : "
                    f"{bos['bos_price']:.2f}"
                )

                print(
                    f"Structure : "
                    f"{bos['structure_level']:.2f}"
                )

                print(
                    f"Time      : "
                    f"{bos['timestamp']}"
                )

                print("=" * 60)


                # =============================================
                # ACTIVATE RETEST
                # =============================================

                m1_retest.set_bos(
                    bos
                )


        # ====================================================
        # M1 RETEST
        # ====================================================

        if (
            active_setup is not None
            and
            bos_detected
            and
            not retest_detected
            and
            not paper_trade.is_active()
        ):

            retest = (
                m1_retest.process_candle(
                    candle
                )
            )


            if retest is not None:

                retest_detected = True


                print()
                print("=" * 60)
                print("✅ M1 RETEST CONFIRMED")
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
                    f"Retest   : "
                    f"{retest['retest_price']:.2f}"
                )

                print(
                    f"Time     : "
                    f"{retest['timestamp']}"
                )

                print("=" * 60)


                # =============================================
                # ACTIVATE ENTRY CONFIRMATION
                # =============================================

                entry_manager.set_retest(
                    retest
                )


        # ====================================================
        # ENTRY CONFIRMATION
        # ====================================================

        if (
            active_setup is not None
            and
            retest_detected
            and
            not entry_taken
            and
            not paper_trade.is_active()
        ):

            trade = (
                entry_manager.process_candle(
                    candle
                )
            )


            if trade is not None:

                # =============================================
                # POSITION SIZE
                # =============================================

                quantity = float(
                    trade.get(
                        "quantity",
                        MAX_LOTS
                    )
                )


                # =============================================
                # CURRENT EQUITY
                # =============================================

                current_equity = (
                    equity_monitor.get_equity()
                )


                # =============================================
                # POSITION SIZE VALIDATION
                # =============================================

                position_allowed = (
                    risk_manager.validate_position_size(
                        quantity
                    )
                )


                # =============================================
                # OPEN POSITION LIMIT
                # =============================================

                open_positions = 0

                if paper_trade.is_active():

                    open_positions = 1


                positions_allowed = (
                    risk_manager.validate_open_positions(
                        open_positions
                    )
                )


                # =============================================
                # RISK VALIDATION
                # =============================================

                risk_allowed = (
                    risk_manager.validate_trade(

                        trade,

                        current_equity,

                        quantity
                    )
                )


                # =============================================
                # FINAL TRADE DECISION
                # =============================================

                if (
                    position_allowed
                    and
                    positions_allowed
                    and
                    risk_allowed
                ):

                    entry_taken = True


                    print()
                    print("=" * 60)
                    print("🚨 TRADE ENTRY ACTIVATED")
                    print("=" * 60)

                    print(
                        f"Side     : "
                        f"{trade['side']}"
                    )

                    print(
                        f"Entry    : "
                        f"{trade['entry']:.2f}"
                    )

                    print(
                        f"SL       : "
                        f"{trade['stop_loss']:.2f}"
                    )

                    print(
                        f"TP       : "
                        f"{trade['take_profit']:.2f}"
                    )

                    print(
                        f"Quantity : "
                        f"{quantity:.2f} lots"
                    )

                    print("=" * 60)


                    # =========================================
                    # PAPER TRADE
                    # =========================================

                    if PAPER_TRADING:

                        # Add quantity to trade
                        trade["quantity"] = quantity

                        paper_trade.open_trade(
                            trade
                        )


                else:

                    print()
                    print("=" * 60)
                    print("❌ TRADE BLOCKED BY RISK MANAGER")
                    print("=" * 60)

                    print(
                        "The strategy generated a signal,"
                    )

                    print(
                        "but the trade did NOT pass "
                        "risk validation."
                    )

                    print("=" * 60)


                    # =========================================
                    # RESET SIGNAL STATE
                    # =========================================

                    active_setup = None

                    bos_detected = False

                    retest_detected = False

                    entry_taken = False


        # ====================================================
        # STATUS
        # ====================================================

        if paper_trade.is_active():

            active_trade = (
                paper_trade.active_trade
            )

            print(
                "STATUS → PAPER TRADE ACTIVE; "
                "monitoring SL/TP..."
            )

            print(
                f"         Entry: "
                f"{active_trade['entry']:.2f}"
            )

            print(
                f"         SL: "
                f"{active_trade['stop_loss']:.2f}"
            )

            print(
                f"         TP: "
                f"{active_trade['take_profit']:.2f}"
            )

            print(
                f"         Equity: "
                f"${equity_monitor.get_equity():.2f}"
            )

            print(
                f"         Floating P&L: "
                f"${equity_monitor.get_floating_pnl():+.2f}"
            )

        elif active_setup is None:

            print(
                "STATUS → Waiting for M30 breakout..."
            )

        elif not bos_detected:

            print(
                "STATUS → Waiting for M1 BOS..."
            )

        elif not retest_detected:

            print(
                "STATUS → Waiting for M1 retest..."
            )

        elif not entry_taken:

            print(
                "STATUS → Waiting for M1 confirmation..."
            )

        else:

            print(
                "STATUS → Trade completed; "
                "waiting for next setup..."
            )


        # ====================================================
        # WAIT
        # ====================================================

        time.sleep(2)


    # ========================================================
    # USER STOP
    # ========================================================

    except KeyboardInterrupt:

        print()
        print("=" * 60)
        print("BOT STOPPED BY USER")
        print("=" * 60)

        break


    # ========================================================
    # ERROR
    # ========================================================

    except Exception as e:

        print()
        print("=" * 60)
        print("BINANCE API / STRATEGY ERROR")
        print("=" * 60)

        print(
            type(e).__name__,
            e
        )

        print(
            "Retrying in 5 seconds..."
        )

        time.sleep(5)