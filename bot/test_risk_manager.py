from risk_manager import RiskManager


# ============================================================
# CREATE RISK MANAGER
# ============================================================

risk_manager = RiskManager(
    risk_percent=0.5,
    max_lots=0.5,
    max_open_positions=1
)


# ============================================================
# TEST EQUITY
# ============================================================

equity = 10000.0


print()
print("=" * 60)
print("RISK MANAGER TEST")
print("=" * 60)

print(
    f"Current Equity : ${equity:.2f}"
)

print(
    f"Risk Limit     : "
    f"{risk_manager.get_risk_percent():.2f}%"
)

print(
    f"Maximum Lots   : "
    f"{risk_manager.get_max_lots():.2f}"
)

print("=" * 60)


# ============================================================
# TEST 1 — VALID TRADE
# ============================================================

trade_1 = {

    "risk": 40.0
}


print()
print("TEST 1 — RISK = $40")

result = risk_manager.validate_trade(
    trade_1,
    equity
)

print(
    "Result:",
    "ALLOWED" if result else "REJECTED"
)


# ============================================================
# TEST 2 — RISK TOO HIGH
# ============================================================

trade_2 = {

    "risk": 60.0
}


print()
print("TEST 2 — RISK = $60")

result = risk_manager.validate_trade(
    trade_2,
    equity
)

print(
    "Result:",
    "ALLOWED" if result else "REJECTED"
)


# ============================================================
# TEST 3 — VALID POSITION SIZE
# ============================================================

print()
print("TEST 3 — POSITION = 0.5 LOTS")

result = risk_manager.validate_position_size(
    0.5
)

print(
    "Result:",
    "ALLOWED" if result else "REJECTED"
)


# ============================================================
# TEST 4 — POSITION TOO LARGE
# ============================================================

print()
print("TEST 4 — POSITION = 0.7 LOTS")

result = risk_manager.validate_position_size(
    0.7
)

print(
    "Result:",
    "ALLOWED" if result else "REJECTED"
)


# ============================================================
# FINISHED
# ============================================================

print()
print("=" * 60)
print("RISK MANAGER TEST COMPLETED")
print("=" * 60)