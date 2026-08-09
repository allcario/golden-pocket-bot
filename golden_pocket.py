"""
Detectielogica voor de Golden Pocket-strategie:
1. Vind swing-highs/lows (fractal-methode).
2. Zoek vanaf het meest recente swing-punt terug naar het dichtstbijzijnde
   swing-punt van het TEGENOVERGESTELDE type waarvan de afstand groot genoeg
   is (minimaal MIN_SWING_ATR_MULT x ATR) - dit filtert kleine, onbeduidende
   "ruis"-swings eruit en zorgt dat alleen structureel grote swings gebruikt
   worden (zoals een mens dat ook zou doen).
3. Bereken de golden pocket-zone (fib 0.5 - 0.618) van die (grote) leg.
4. Check of de laatste (gesloten) candle in die zone komt EN weer terugkeert
   (rejectie) in de richting van de oorspronkelijke leg - dat is de entry.

Omdat we ALTIJD vanaf het meest recente punt zoeken, "beweegt" de fib vanzelf
mee zodra er een nieuwe, verdere swing ontstaat.
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


def compute_atr(df: pd.DataFrame, length: int) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(length).mean()


def detect_golden_pocket(df: pd.DataFrame, cfg) -> dict:
    n = len(df)
    last_idx = n - 1
    last = df.iloc[-1]

    lookback_start = max(0, n - cfg.SWING_LOOKBACK)
    sub_df = df.iloc[lookback_start:n].reset_index(drop=True)
    offset = lookback_start

    swing_high_idx, swing_low_idx = find_swing_points(sub_df, cfg.FRACTAL_N)
    atr_series = compute_atr(df, cfg.ATR_LEN)
    current_atr = atr_series.iloc[-1]

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
        "swing_range_pct": None,
        "close": float(last["close"]),
    }

    if pd.isna(current_atr) or current_atr <= 0:
        return result

    min_swing_size = cfg.MIN_SWING_ATR_MULT * current_atr

    # Combineer alle swing-punten (beide types) chronologisch, met hun type
    all_points = (
        [(offset + i, sub_df["high"].iloc[i], "high") for i in swing_high_idx if (offset + i) < last_idx] +
        [(offset + i, sub_df["low"].iloc[i], "low") for i in swing_low_idx if (offset + i) < last_idx]
    )
    all_points.sort(key=lambda x: x[0])  # oplopend op index (chronologisch)

    if len(all_points) < 2:
        return result

    # Het meest recente swing-punt = het "einde" van de huidige leg
    anchor_end = all_points[-1]
    end_idx, end_price, end_type = anchor_end

    # Zoek terug (van dichtbij naar ver) naar het eerste punt van het
    # TEGENOVERGESTELDE type waarvan de range groot genoeg is
    anchor_start = None
    for point in reversed(all_points[:-1]):
        idx, price, ptype = point
        if ptype == end_type:
            continue  # zelfde type, geen geldige leg-start
        if abs(end_price - price) >= min_swing_size:
            anchor_start = point
            break

    if anchor_start is None:
        return result  # geen enkele leg groot genoeg gevonden

    start_idx, start_price, start_type = anchor_start

    if end_type == "high":
        # Leg ging OMHOOG (low -> high) -> golden pocket voor een LONG-retracement
        swing_low_idx_final, swing_low_price = start_idx, start_price
        swing_high_idx_final, swing_high_price = end_idx, end_price
    else:
        # Leg ging OMLAAG (high -> low) -> golden pocket voor een SHORT-retracement
        swing_high_idx_final, swing_high_price = start_idx, start_price
        swing_low_idx_final, swing_low_price = end_idx, end_price

    result["swing_high_index"] = swing_high_idx_final
    result["swing_high_price"] = float(swing_high_price)
    result["swing_low_index"] = swing_low_idx_final
    result["swing_low_price"] = float(swing_low_price)

    rng = swing_high_price - swing_low_price
    if rng <= 0:
        return result

    result["swing_range_pct"] = float(rng / swing_low_price * 100)

    if end_type == "high":
        result["leg_direction"] = "UP"
        zone_high = swing_high_price - cfg.FIB_GOLDEN_LOW * rng
        zone_low = swing_high_price - cfg.FIB_GOLDEN_HIGH * rng
        result["zone_low"] = float(zone_low)
        result["zone_high"] = float(zone_high)

        entered_zone = last["low"] <= zone_high and last["high"] >= zone_low
        rejected_up = last["close"] > zone_high
        if entered_zone and rejected_up:
            result["long_signal"] = True

    else:
        result["leg_direction"] = "DOWN"
        zone_low = swing_low_price + cfg.FIB_GOLDEN_LOW * rng
        zone_high = swing_low_price + cfg.FIB_GOLDEN_HIGH * rng
        result["zone_low"] = float(zone_low)
        result["zone_high"] = float(zone_high)

        entered_zone = last["high"] >= zone_low and last["low"] <= zone_high
        rejected_down = last["close"] < zone_low
        if entered_zone and rejected_down:
            result["short_signal"] = True

    return result
