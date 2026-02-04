# Trading Bot Configuration
# Copy this file to config.py and fill in your API keys

# Paper Trading Settings
INITIAL_BALANCE = 1000.0  # Starting balance for paper trading

# Risk Management
MAX_DAILY_LOSS_PCT = 5.0  # Stop trading if daily loss exceeds 5%
MAX_POSITION_PCT = 2.0    # Max 2% of portfolio per trade
MAX_TRADES_PER_DAY = 10   # Limit trades per day

# Trading Settings
CHECK_INTERVAL = 60       # Check for signals every 60 seconds
STOP_LOSS_PCT = 1.0       # 1% stop loss
TAKE_PROFIT_PCT = 2.0     # 2% take profit

# Symbols to Trade
TRADING_SYMBOLS = [
    'BTCUSDT',   # Bitcoin
    'ETHUSDT',   # Ethereum
    'SOLUSDT',   # Solana
]

# Technical Analysis Settings
SMA_SHORT = 10      # 10-period SMA
SMA_MEDIUM = 20     # 20-period SMA
SMA_LONG = 50       # 50-period SMA
EMA_SHORT = 12      # 12-period EMA
EMA_LONG = 26       # 26-period EMA
VOLUME_THRESHOLD = 2.0  # Volume spike threshold (2x average)

# Signal Confidence Threshold
MIN_CONFIDENCE = 0.6  # Minimum confidence to trade

# API Keys (ONLY FILL WHEN READY FOR LIVE TRADING)
# For now, bot uses free Binance API (no keys needed for price data)
BINANCE_API_KEY = ""
BINANCE_SECRET_KEY = ""

# Notification Settings (optional)
ENABLE_NOTIFICATIONS = False
DISCORD_WEBHOOK_URL = ""

# Logging
LOG_LEVEL = "INFO"
LOG_TO_FILE = True
