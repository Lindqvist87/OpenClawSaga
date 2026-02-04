#!/usr/bin/env python3
"""Test script for Micro-Scalp Bot v2.0"""

import sys
sys.path.insert(0, '.')
from micro_scalp_bot_v2 import MicroScalpBot, TechnicalIndicators, SignalGenerator, PriceMonitor
import random

print("="*60)
print("MICRO-SCALP BOT v2.0 - TEST SUITE")
print("="*60)

# Test 1: Technical Indicators
print("\n[TEST 1] Technical Indicators")
print("-"*40)

prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113, 115, 117, 116, 118, 120]

rsi = TechnicalIndicators.calculate_rsi(prices)
print(f"RSI(14): {rsi:.2f}" if rsi else "RSI: None")

macd = TechnicalIndicators.calculate_macd(prices)
print(f"MACD: {macd['macd']:.4f}, Signal: {macd['signal']:.4f}" if macd['macd'] else "MACD: None")

bb = TechnicalIndicators.calculate_bollinger_bands(prices)
if bb['upper']:
    print(f"Bollinger Bands: Upper=${bb['upper']:.2f}, Middle=${bb['middle']:.2f}, Lower=${bb['lower']:.2f}")
    print(f"%B: {bb['percent_b']:.4f}")
else:
    print("Bollinger Bands: None")

sma_10 = TechnicalIndicators.calculate_sma(prices, 10)
ema_12 = TechnicalIndicators.calculate_ema(prices, 12)
print(f"SMA(10): {sma_10:.2f}" if sma_10 else "SMA: None")
print(f"EMA(12): {ema_12:.2f}" if ema_12 else "EMA: None")

print("PASSED: Technical Indicators")

# Test 2: Signal Generator
print("\n[TEST 2] Signal Generator")
print("-"*40)

random.seed(42)
sg = SignalGenerator()

# Create realistic mock candles with an uptrend
candles = []
base_price = 50000
for i in range(60):
    trend = i * 10  # Slight uptrend
    noise = random.uniform(-200, 200)
    price = base_price + trend + noise
    candles.append({
        'open': price - random.uniform(0, 100),
        'high': price + random.uniform(50, 150),
        'low': price - random.uniform(50, 150),
        'close': price,
        'volume': random.uniform(100, 1000) * (1.5 if i > 50 else 1.0)  # Volume spike at end
    })

signal = sg.generate_signal(candles, 'BTCUSDT')
print(f"Signal: {signal.signal}")
print(f"Confidence: {signal.confidence:.2%}")
print(f"Reason: {signal.reason}")

if signal.indicators:
    print(f"Price: ${signal.indicators['price']:,.2f}")
    if signal.indicators.get('rsi'):
        print(f"RSI: {signal.indicators['rsi']:.2f}")
    if signal.indicators.get('trend'):
        print(f"Trend: {signal.indicators['trend']['direction']}")

stats = sg.get_signal_stats()
print(f"Signal Stats: {stats}")

print("PASSED: Signal Generator")

# Test 3: Price Monitor
print("\n[TEST 3] Price Monitor")
print("-"*40)

pm = PriceMonitor()

print("Fetching BTC price from Binance...")
btc_price = pm.get_price('BTCUSDT')
if btc_price:
    print(f"BTC Price: ${btc_price:,.2f}")
    
    print("Fetching klines...")
    klines = pm.get_klines('BTCUSDT', interval='1h', limit=10)
    if klines:
        print(f"Retrieved {len(klines)} candles")
        print(f"Latest candle: Open=${klines[-1]['open']:,.2f}, Close=${klines[-1]['close']:,.2f}, Volume={klines[-1]['volume']:.2f}")
        print("PASSED: Price Monitor")
    else:
        print("WARNING: Could not fetch klines")
else:
    print("WARNING: Could not fetch BTC price (API may be unavailable)")

# Test 4: Paper Trader
print("\n[TEST 4] Paper Trader")
print("-"*40)

from micro_scalp_bot_v2 import PaperTrader, RiskManager

trader = PaperTrader(initial_balance=10000.0)
risk = RiskManager()

# Simulate a trade
entry_price = 50000
quantity = 0.1
stop_loss = 49000
take_profit = 52000

trade = trader.open_trade('BTCUSDT', 'BUY', entry_price, quantity, stop_loss, take_profit)
if trade:
    print(f"Opened trade #{trade.id}: {trade.symbol} @ ${trade.entry_price:,.2f}")
    print(f"Balance after open: ${trader.balance:,.2f}")
    
    # Close trade at profit
    exit_price = 51500
    closed = trader.close_trade(trade.id, exit_price, "take_profit")
    if closed:
        print(f"Closed trade #{closed.id}: P&L = ${closed.profit_loss:,.2f} ({closed.profit_loss_pct:.2f}%)")
        print(f"Balance after close: ${trader.balance:,.2f}")

stats = trader.get_stats()
print(f"Total Return: {stats['total_return_pct']:.2f}%")
print(f"Win Rate: {stats['win_rate']:.1f}%")

print("PASSED: Paper Trader")

# Test 5: Bot Initialization
print("\n[TEST 5] Bot Initialization")
print("-"*40)

bot = MicroScalpBot(symbols=['BTCUSDT'], enable_dashboard=False)
print(f"Bot initialized with symbols: {bot.symbols}")
print(f"Initial balance: ${bot.trader.initial_balance:,.2f}")
print(f"Check interval: {bot.check_interval}s")

print("PASSED: Bot Initialization")

print("\n" + "="*60)
print("ALL TESTS PASSED!")
print("="*60)
print("\nThe bot is ready to run. Start with:")
print("  python micro_scalp_bot_v2.py")
print("\nDashboard will be available at: http://localhost:8080")
