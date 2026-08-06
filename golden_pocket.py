"""
Detectielogica voor de Golden Pocket-strategie:
1. Vind de meest RECENTE swing-high en swing-low (fractal-methode, zelfde
   als de liquidity-grab-bot) - dit bepaalt de "actuele leg" (beweging).
2. Bepaal of de actuele leg omhoog (low->high) of omlaag (high->low) ging.
3. Bereken de golden pocket-zone (fib 0.5 - 0.618 retracement) van die leg.
4. Check of de laatste (gesloten) candle in die zone komt EN weer terugkeert
   (rejectie) in de richting van de oorspronkelijke leg - dat is de entry.

Omdat we ALTIJD de meest recente swing high/low gebruiken, "beweegt" de fib
vanzelf mee zodra er een nieuwe, verdere swing ontstaat - er hoeft niks
handmatig te worden vastgehouden aan een oude swing.
"""

import numpy as np
import pandas as pd


def find_swing_points(df: pd.DataFrame, fractal_n: int) -> tuple:
    highs = df["high"].values
    lows = df["low"].values
    n = len(df)

    swing_high_idx = []
    swing_low_idx = []

    for i in range(fractal_n, n - fractal_n):
        window_high = highs[i - fractal_n: i + fractal_n + 1]
        if highs[i] == window_high.max() and np.sum(window_high == highs[i]) == 1:
            swing_high_idx.append(i)

        window_low = lows[i - fractal_n: i + fractal_n + 1]
        if lows[i] == window_low.min() and np.sum(window_low == lows[i]) == 1:
            swing_low_idx.append(i)

    return swing_high_idx, swing_low_idx


def detect_golden_pocket(df: pd.DataFrame, cfg) -> dict:
    n = len(df)
    last_idx = n - 1
    last = df.iloc[-1]

    lookback_start = max(0, n - cfg.SWING_LOOKBACK)
    sub_df = df.iloc[lookback_start:n].reset_index(drop=True)
    offset = lookback_start

    swing_high_idx, swing_low_idx = find_swing_points(sub_df, cfg.FRACTAL_N)

    result = {
        "long_signal": False,
        "short_signal": False,
        "zone_low": None,
        "zone_high": None,
        "swing_high_index": None,
        "swing_high_price": None,
        "swing_low_index": None,
        "swing_low_price": None,
        "leg_direction": None,
        "close": float(last["close"]),
    }

    valid_highs = [(offset + i, sub_df["high"].iloc[i]) for i in swing_high_idx if (offset + i) < last_idx]
    valid_lows = [(offset + i, sub_df["low"].iloc[i]) for i in swing_low_idx if (offset + i) < last_idx]

    if not valid_highs or not valid_lows:
        return result

    latest_high_idx, latest_high_price = max(valid_highs, key=lambda x: x[0])
    latest_low_idx, latest_low_price = max(valid_lows, key=lambda x: x[0])

    result["swing_high_index"] = latest_high_idx
    result["swing_high_price"] = float(latest_high_price)
    result["swing_low_index"] = latest_low_idx
    result["swing_low_price"] = float(latest_low_price)

    rng = latest_high_price - latest_low_price
    if rng <= 0:
        return result

    if latest_high_idx > latest_low_idx:
        result["leg_direction"] = "UP"
        zone_high = latest_high_price - cfg.FIB_GOLDEN_LOW * rng
        zone_low = latest_high_price - cfg.FIB_GOLDEN_HIGH * rng
        result["zone_low"] = float(zone_low)
        result["zone_high"] = float(zone_high)

        entered_zone = last["low"] <= zone_high and last["high"] >= zone_low
        rejected_up = last["close"] > zone_high
        if entered_zone and rejected_up:
            result["long_signal"] = True

    else:
        result["leg_direction"] = "DOWN"
        zone_low = latest_low_price + cfg.FIB_GOLDEN_LOW * rng
        zone_high = latest_low_price + cfg.FIB_GOLDEN_HIGH * rng
        result["zone_low"] = float(zone_low)
        result["zone_high"] = float(zone_high)

        entered_zone = last["high"] >= zone_low and last["low"] <= zone_high
        rejected_down = last["close"] < zone_low
        if entered_zone and rejected_down:
            result["short_signal"] = True

    return result
