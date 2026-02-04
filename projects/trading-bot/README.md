# Micro-Scalp Trading Bot v2.0

## Overview

An enhanced paper trading bot for cryptocurrency scalp trading with comprehensive technical indicators, backtesting, and real-time dashboard monitoring.

**⚠️ PAPER TRADING ONLY - NO REAL MONEY IS USED ⚠️**

## Features

### Technical Indicators
- **SMA** (10, 20, 50 period) - Simple Moving Averages
- **EMA** (12, 26 period) - Exponential Moving Averages
- **RSI** (14 period) - Relative Strength Index for overbought/oversold detection
- **MACD** (12/26/9) - Moving Average Convergence Divergence with histogram
- **Bollinger Bands** (20 period, 2 std dev) - Volatility bands with %B indicator
- **Stochastic Oscillator** (14/3) - Momentum indicator
- **ATR** (14 period) - Average True Range for volatility-based stops
- **Volume Profile** - Volume-based support/resistance levels

### Signal Generation
- Multi-indicator scoring system (weighted signals)
- Confidence-based trading (minimum 60% confidence required)
- Volume spike detection with trend confirmation
- Automatic signal validation with multiple confirmations

### Risk Management
- Dynamic position sizing based on:
  - Signal confidence
  - Volatility (ATR adjustment)
  - Portfolio value
- ATR-based stop losses (2x ATR default)
- Risk:Reward ratio targeting (2:1 default)
- Daily loss limits (3% default)
- Maximum trades per day (10 default)
- Real-time P&L tracking

### Backtesting
- Historical data backtesting capability
- Performance metrics:
  - Win rate
  - Total return
  - Max drawdown
  - Profit factor
  - Sharpe ratio

### Dashboard & Reporting
- Real-time web dashboard (http://localhost:8080)
- Auto-refreshing metrics
- Open trade monitoring
- Risk status tracking
- API health monitoring
- Comprehensive statistics

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Run the bot with default settings
python micro_scalp_bot_v2.py
```

### Configuration

Edit the bot initialization to customize:

```python
bot = MicroScalpBot(
    symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],  # Trading pairs
    enable_dashboard=True  # Enable web dashboard
)
```

### Risk Management Settings

```python
risk_manager = RiskManager(
    max_daily_loss_pct=3.0,      # Max 3% daily loss
    max_position_pct=5.0,        # Max 5% per position
    max_trades_per_day=10,       # Max 10 trades/day
    atr_multiplier_sl=2.0,       # Stop loss at 2x ATR
    risk_reward_ratio=2.0        # 2:1 reward to risk
)
```

### Running Backtest

```python
# Run backtest before live trading
bot = MicroScalpBot()
results = bot.run_backtest('BTCUSDT', days=30)
```

## Project Structure

```
projects/trading-bot/
├── micro_scalp_bot.py          # Original bot (v1.0)
├── micro_scalp_bot_v2.py       # Enhanced bot (v2.0)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── trading_bot.log            # Bot logs
└── paper_trades.db            # SQLite database with trades
```

## Database Schema

### trades table
- id, symbol, side, entry_price, exit_price
- quantity, profit_loss, profit_loss_pct
- entry_time, exit_time, status, strategy
- stop_loss, take_profit

### performance table
- timestamp, balance, equity
- open_trades, total_trades

## Trading Strategy

The bot uses a multi-factor scoring system:

1. **Trend Analysis** (weight: 2)
   - Bullish: SMA10 > SMA20 > SMA50
   - Bearish: SMA10 < SMA20 < SMA50

2. **RSI Analysis** (weight: 2)
   - Oversold (< 30): Buy signal
   - Overbought (> 70): Sell signal

3. **MACD Analysis** (weight: 2)
   - Bullish crossover: Buy signal
   - Bearish crossover: Sell signal

4. **Bollinger Bands** (weight: 1.5)
   - Near lower band: Buy signal
   - Near upper band: Sell signal

5. **Volume Analysis** (weight: 1.5)
   - Volume spike + trend direction

6. **Stochastic** (weight: 1)
   - Oversold/overbought detection

7. **EMA Crossover** (weight: 1)
   - EMA12 vs EMA26

**Signal Threshold**: 60% confidence required to trade

## Performance Metrics

The bot tracks:
- Win rate
- Total P&L
- Average profit/loss per trade
- Profit factor
- Maximum drawdown
- Sharpe ratio
- Total return percentage

## Safety Features

1. **Paper Trading Only**: No real API keys for trading
2. **Daily Loss Limits**: Trading stops after hitting limit
3. **Position Limits**: Maximum exposure per trade
4. **Stop Losses**: Automatic ATR-based stops
5. **Error Handling**: Graceful handling of API failures
6. **Rate Limiting**: Respects API limits

## Monitoring

### Console Output
Real-time status printed every 5 cycles:
- Balance and equity
- Win rate and P&L
- Open trades with unrealized P&L
- Risk metrics

### Web Dashboard
Available at http://localhost:8080:
- Real-time metrics
- Auto-refresh (10 seconds)
- Open trade details
- Risk status
- Signal statistics
- API health

### Logs
All activity logged to `trading_bot.log`:
- Trade entries/exits
- Signal generation
- Errors and warnings
- Performance snapshots

## Improvements from v1.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Indicators | SMA, EMA, Volume | RSI, MACD, Bollinger, Stochastic, ATR |
| Signal Scoring | Basic | Multi-factor weighted |
| Position Sizing | Fixed % | Dynamic (confidence + ATR) |
| Stop Loss | Fixed 1% | ATR-based (2x ATR) |
| Backtesting | No | Yes |
| Dashboard | No | Yes (web) |
| Risk Management | Basic | Enhanced with limits |
| Database | Trades only | Trades + Performance |
| Logging | Basic | Rotating file handler |
| Fee Simulation | No | Yes (0.1%) |

## Troubleshooting

### No signals generated
- Check API connectivity
- Verify symbol exists on Binance
- Ensure sufficient historical data (50+ candles)

### Dashboard not accessible
- Check firewall settings
- Verify port 8080 is available
- Try different port in DashboardServer

### Database errors
- Delete `paper_trades.db` to reset
- Check file permissions

## Future Enhancements

Potential improvements:
- Machine learning signal prediction
- Multi-timeframe analysis
- Portfolio optimization
- Telegram/discord notifications
- More exchanges support
- Real trading mode (with proper safeguards)

## License

Personal use only. Not financial advice.

## Disclaimer

**IMPORTANT**: This is a paper trading bot for educational purposes only.
- Past performance does not guarantee future results
- Cryptocurrency trading carries significant risk
- Always test thoroughly before using real funds
- The authors are not responsible for any losses
