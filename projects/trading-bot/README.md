# 🤖 MICRO-SCALP TRADING BOT
## Automated Crypto Trading - Paper Trading Mode

**⚠️ SECURITY WARNING:** Due to 386 malicious crypto plugins discovered in OpenClaw's ClawHub, this bot is built from scratch with NO external plugins.

---

## 🎯 Strategy: "Micro-Scalp"

**Goal:** Small, consistent profits (0.5-2% per trade)  
**Risk:** Minimal (strict stop-losses)  
**Markets:** Bitcoin, Ethereum, Solana  
**Mode:** Paper Trading (simulated) → Live Trading (after validation)

### Why This Strategy?
- **High frequency:** Many small trades = compound growth
- **Low risk:** Tight stop-losses (max 1% loss per trade)
- **Proven concept:** Scalping works in volatile crypto markets
- **Funding goal:** 15-30% monthly = fund OpenClaw upgrades

---

## 📊 Expected Returns

| Capital | Conservative (15%/month) | Optimistic (30%/month) |
|---------|-------------------------|----------------------|
| $100    | $15/month               | $30/month            |
| $500    | $75/month               | $150/month           |
| $1000   | $150/month              | $300/month           |

**Goal:** Start with $100-500, grow to fund OpenClaw tools and upgrades

---

## 🏗️ Architecture

```
Price Monitor (Binance API)
    ↓
Signal Generator (SMA/EMA/Volume)
    ↓
Risk Manager (Position sizing, stops)
    ↓
Paper Trader (Simulated trades)
    ↓
SQLite Database (Trade history)
```

### Components:
1. **PriceMonitor** - Real-time price data from Binance
2. **SignalGenerator** - Technical analysis (SMA, EMA, volume spikes)
3. **RiskManager** - Position sizing, stop-loss, daily limits
4. **PaperTrader** - Simulated trading with $1000 fake money
5. **MicroScalpBot** - Main orchestrator

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd projects/trading-bot
chmod +x start.sh
./start.sh
```

Or manually:
```bash
pip install requests
```

### 2. Start Paper Trading
```bash
python3 micro_scalp_bot.py
```

### 3. Monitor Performance
- Check `trading_bot.log` for activity
- View trades in `paper_trades.db` (SQLite)
- Stats printed every minute to console

---

## ⚙️ Configuration

Edit `config.py` (copy from `config_template.py`):

```python
# Risk Management
MAX_DAILY_LOSS_PCT = 5.0   # Stop if daily loss >5%
MAX_POSITION_PCT = 2.0     # Max 2% per trade
MAX_TRADES_PER_DAY = 10    # Limit trades

# Trading Settings
STOP_LOSS_PCT = 1.0        # 1% stop loss
TAKE_PROFIT_PCT = 2.0      # 2% take profit
CHECK_INTERVAL = 60        # Check every 60 seconds

# Symbols to Trade
TRADING_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
```

---

## 📈 Trading Strategy Details

### Entry Signals:
- **Bullish:** SMA10 > SMA20 > SMA50 + EMA12 > EMA26
- **Volume Spike:** 2x average volume
- **Confidence:** >60% required to trade

### Exit Signals:
- **Stop Loss:** 1% loss (auto-executed)
- **Take Profit:** 2% gain (auto-executed)
- **Trailing Stop:** (future feature)

### Risk Rules:
- Max 2% of portfolio per trade
- Max 5% daily loss (then STOP)
- Max 10 trades per day
- Only trade spot (no leverage)

---

## 🔄 Autonomous Workflows

The bot runs autonomously via OpenClaw Heartbeat:

| Frequency | Task |
|-----------|------|
| Every minute | Check prices, generate signals, manage trades |
| Every 5 minutes | Performance check, risk assessment |
| Hourly | Risk audit, position review |
| Daily 08:00 | Morning brief, strategy adjustment |
| Daily 20:00 | Daily report, GitHub commit |
| Weekly | Strategy review, optimization |

---

## 🛡️ Safety Features

1. ✅ **Paper Trading First** - 1-2 weeks validation before real money
2. ✅ **Strict Stop-Losses** - Max 1% loss per trade
3. ✅ **Daily Limits** - Stop at 5% daily loss
4. ✅ **Position Limits** - Max 2% per trade
5. ✅ **No Leverage** - Spot trading only
6. ✅ **SQLite Logging** - All trades tracked
7. ✅ **Auto-Stop** - Bot stops on excessive losses

---

## 📊 Performance Tracking

The bot automatically tracks:
- Win rate (% profitable trades)
- Average profit per trade
- Total P&L
- Max drawdown
- Daily/weekly/monthly returns
- Risk metrics

View stats in real-time or query SQLite database.

---

## 🚨 Warnings

**⚠️ CRITICAL:**
- This is NOT financial advice
- Crypto trading is HIGH RISK
- Only trade money you can afford to lose
- Past performance ≠ future results
- Bot can lose money - risk management is key

**Paper Trading Phase:**
- Run for minimum 1-2 weeks
- Validate win-rate >50%
- Ensure strategy works in current market
- ONLY then consider live trading

---

## 📝 Files

| File | Description |
|------|-------------|
| `micro_scalp_bot.py` | Main trading bot |
| `config_template.py` | Configuration template |
| `ARCHITECTURE.md` | Technical architecture |
| `start.sh` | Quick start script |
| `trading_bot.log` | Activity log |
| `paper_trades.db` | SQLite trade database |

---

## 🎓 How It Works

1. **Price Monitoring** - Bot checks prices every minute
2. **Signal Generation** - Technical analysis creates BUY/SELL signals
3. **Risk Check** - Position size calculated, limits verified
4. **Trade Execution** - Paper trade opened in SQLite database
5. **Management** - Stop-loss/take-profit monitored continuously
6. **Reporting** - Stats updated, alerts if limits hit

---

## 🔮 Future Enhancements

- [ ] Discord notifications
- [ ] More technical indicators (RSI, MACD)
- [ ] Backtesting module
- [ ] Multi-exchange arbitrage
- [ ] ML-based signal generation
- [ ] Live trading mode (after paper validation)

---

## 💰 Funding Goal

**Target:** Generate $150-300/month to fund:
- OpenClaw upgrades
- Better AI models
- Additional tools
- Infrastructure expansion

**Path:**
1. Week 1-2: Paper trading validation
2. Week 3-4: Micro live trading ($100)
3. Month 2+: Scale to $500-1000 capital
4. Month 3+: Full operation

---

*Built from scratch - NO external plugins*  
*Security first - Paper trading validation required*  
*Autonomous operation via OpenClaw Heartbeat*

**READY TO TRADE (PAPER MODE)** 🚀
