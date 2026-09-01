import pandas as pd
from pathlib import Path


# ============================================================
# FILES
# ============================================================

INPUT_FILE = Path(
    "data/processed/XAUUSDT-M1-confirmations.csv"
)

OUTPUT_FILE = Path(
    "data/processed/XAUUSDT-M1-valid-confirmations.csv"
)


# ============================================================
# VALIDATION SETTINGS
# ============================================================

# Maximum acceptable distance between the M30 liquidity
# breakout level and the M1 structure level.
#
# This prevents a completely unrelated M1 structure break
# from being attached to an M30 breakout.
MAX_BOS_DISTANCE = 15.0

# Maximum time allowed between M30 breakout and M1 BOS.
MAX_BOS_DELAY_MINUTES = 30

# Maximum time allowed between M1 BOS and M1 retest.
MAX_RETEST_DELAY_MINUTES = 30

# Maximum distance between entry and the broken M1 structure level.
MAX_ENTRY_DISTANCE = 3.0


# ============================================================
# LOAD
# ============================================================

print("======================================")
print("     M1 CONFIRMATION VALIDATOR")
print("======================================")

print("\nLoading confirmations...")

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=[
        "breakout_time",
        "structure_break_time",
        "retest_time"
    ]
)

print(
    f"Confirmations loaded: {len(df)}"
)


# ============================================================
# VALIDATE
# ============================================================

valid_rows = []
rejected_rows = []

for _, row in df.iterrows():

    breakout_time = row["breakout_time"]
    bos_time = row["structure_break_time"]
    retest_time = row["retest_time"]

    liquidity_price = float(
        row["liquidity_price"]
    )

    structure_level = float(
        row["structure_level"]
    )

    entry_price = float(
        row["entry_price"]
    )

    direction = row["direction"]


    # ========================================================
    # 1. BOS DELAY
    # ========================================================

    bos_delay = (
        bos_time - breakout_time
    ).total_seconds() / 60.0

    if bos_delay < 0:
        rejected_rows.append({
            **row.to_dict(),
            "rejection_reason":
                "BOS before M30 breakout"
        })
        continue

    if bos_delay > MAX_BOS_DELAY_MINUTES:
        rejected_rows.append({
            **row.to_dict(),
            "rejection_reason":
                "BOS too late"
        })
        continue


    # ========================================================
    # 2. BOS DISTANCE FROM M30 LIQUIDITY
    # ========================================================

    bos_distance = abs(
        structure_level -
        liquidity_price
    )

    if bos_distance > MAX_BOS_DISTANCE:
        rejected_rows.append({
            **row.to_dict(),
            "rejection_reason":
                "M1 BOS too far from M30 liquidity"
        })
        continue


    # ========================================================
    # 3. RETEST DELAY
    # ========================================================

    retest_delay = (
        retest_time - bos_time
    ).total_seconds() / 60.0

    if retest_delay <= 0:
        rejected_rows.append({
            **row.to_dict(),
            "rejection_reason":
                "Retest before BOS"
        })
        continue

    if retest_delay > MAX_RETEST_DELAY_MINUTES:
        rejected_rows.append({
            **row.to_dict(),
            "rejection_reason":
                "Retest too late"
        })
        continue


    # ========================================================
    # 4. ENTRY DISTANCE FROM BOS
    # ========================================================

    entry_distance = abs(
        entry_price -
        structure_level
    )

    if entry_distance > MAX_ENTRY_DISTANCE:
        rejected_rows.append({
            **row.to_dict(),
            "rejection_reason":
                "Entry too far from BOS level"
        })
        continue


    # ========================================================
    # VALID
    # ========================================================

    valid_rows.append({
        **row.to_dict(),
        "bos_delay_minutes":
            round(bos_delay, 2),
        "bos_distance":
            round(bos_distance, 2),
        "retest_delay_minutes":
            round(retest_delay, 2),
        "entry_distance":
            round(entry_distance, 2),
        "validation":
            "VALID"
    })


# ============================================================
# DATAFRAMES
# ============================================================

valid_df = pd.DataFrame(
    valid_rows
)

rejected_df = pd.DataFrame(
    rejected_rows
)


# ============================================================
# SAVE VALID SIGNALS
# ============================================================

valid_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# RESULTS
# ============================================================

print("\n======================================")
print("       VALIDATION RESULTS")
print("======================================")

print(
    f"Original confirmations : {len(df)}"
)

print(
    f"Valid confirmations     : {len(valid_df)}"
)

print(
    f"Rejected confirmations  : {len(rejected_df)}"
)


if not valid_df.empty:

    buy_count = (
        valid_df["signal"] == "BUY"
    ).sum()

    sell_count = (
        valid_df["signal"] == "SELL"
    ).sum()

    print(
        f"Valid BUY              : {buy_count}"
    )

    print(
        f"Valid SELL             : {sell_count}"
    )


# ============================================================
# REJECTION REASONS
# ============================================================

if not rejected_df.empty:

    print("\nRejection reasons:")

    print(
        rejected_df[
            "rejection_reason"
        ].value_counts()
    )


# ============================================================
# SHOW VALID SIGNALS
# ============================================================

if not valid_df.empty:

    print("\nFirst 20 VALID confirmations:")

    columns = [
        "breakout_time",
        "liquidity_price",
        "direction",
        "structure_break_time",
        "structure_level",
        "retest_time",
        "entry_price",
        "signal",
        "bos_delay_minutes",
        "bos_distance",
        "retest_delay_minutes",
        "entry_distance"
    ]

    print(
        valid_df[
            columns
        ].head(20).to_string(
            index=False
        )
    )


# ============================================================
# SAVE REJECTED SIGNALS TOO
# ============================================================

REJECTED_FILE = Path(
    "data/processed/XAUUSDT-M1-rejected-confirmations.csv"
)

rejected_df.to_csv(
    REJECTED_FILE,
    index=False
)


print(
    f"\nValid signals saved to:"
)

print(
    OUTPUT_FILE
)

print(
    "\nRejected signals saved to:"
)

print(
    REJECTED_FILE
)

print(
    "\n======================================"
)