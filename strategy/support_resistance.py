import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/XAUUSDT-5m-combined.csv")

LOOKBACK = 15


def find_swing_highs(df, lookback=LOOKBACK):
    """
    Returns information about confirmed swing highs.

    A swing high at index i requires:
        lookback candles before it
        +
        lookback candles after it

    Therefore the swing becomes known only at:
        i + lookback

    The returned Series marks the CANDLE WHERE THE SWING
    BECOMES KNOWN, not the original swing candle.
    """

    highs = df["high"]

    confirmed = pd.Series(
        False,
        index=df.index,
        dtype=bool
    )

    for i in range(
        lookback,
        len(df) - lookback
    ):

        window = highs.iloc[
            i - lookback:
            i + lookback + 1
        ]

        if highs.iloc[i] == window.max():

            confirmation_index = i + lookback

            confirmed.iloc[
                confirmation_index
            ] = True

    return confirmed


def find_swing_lows(df, lookback=LOOKBACK):
    """
    Same logic as swing highs, but for lows.
    """

    lows = df["low"]

    confirmed = pd.Series(
        False,
        index=df.index,
        dtype=bool
    )

    for i in range(
        lookback,
        len(df) - lookback
    ):

        window = lows.iloc[
            i - lookback:
            i + lookback + 1
        ]

        if lows.iloc[i] == window.min():

            confirmation_index = i + lookback

            confirmed.iloc[
                confirmation_index
            ] = True

    return confirmed


if __name__ == "__main__":

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["open_time"]
    )

    df["swing_high_confirmed"] = (
        find_swing_highs(df)
    )

    df["swing_low_confirmed"] = (
        find_swing_lows(df)
    )

    print(
        f"Confirmed swing highs: "
        f"{df['swing_high_confirmed'].sum()}"
    )

    print(
        f"Confirmed swing lows: "
        f"{df['swing_low_confirmed'].sum()}"
    )