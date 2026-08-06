"""
Configuratie voor de Golden Pocket bot.
"""

EXCHANGE = "kraken"

USE_TOP_N_BY_VOLUME = True
TOP_N = 100
QUOTE_CURRENCY = "USD"
COINS = ["BTC/USD", "ETH/USD"]

TIMEFRAMES = ["30m", "1h", "4h", "12h", "1d"]

CANDLE_LIMIT = 200

# ================= SWING / FIB SETTINGS =================
FRACTAL_N = 5

FIB_GOLDEN_LOW = 0.5
FIB_GOLDEN_HIGH = 0.618

SWING_LOOKBACK = 150

# ================= CHART-AFBEELDING SETTINGS =================
SEND_CHART_IMAGE = True
CHART_LOOKBACK = 60

STATE_FILE_TEMPLATE = "state-{timeframe}.json"
