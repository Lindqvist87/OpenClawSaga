#!/usr/bin/env python3
"""
Trading Bot Data Collection Script
Fetches prices, updates DB, generates signals, manages trades
"""

import json
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime

# Fetch current prices from Binance
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
prices = {}

print('[BOT] Fetching prices from Binance...')
for symbol in symbols:
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            prices[symbol] = {
                'price': float(data['lastPrice']),
                'change_24h': float(data['priceChangePercent']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'volume': float(data['volume'])
            }
            print(f"  {symbol}: ${prices[symbol]['price']:,.2f} ({prices[symbol]['change_24h']:+.2f}%)")
    except Exception as e:
        print(f"  Error fetching {symbol}: {e}")

# Check database for trades
print('\n[BOT] Checking paper_trades.db...')
conn = sqlite3.connect('paper_trades.db')
cursor = conn.cursor()

# Get all trades
cursor.execute('SELECT * FROM trades ORDER BY entry_time DESC')
trades = cursor.fetchall()
print(f"  Total trades in DB: {len(trades)}")

# Get open trades
cursor.execute("SELECT * FROM trades WHERE status='OPEN'")
open_trades = cursor.fetchall()
print(f"  Open trades: {len(open_trades)}")

# Get closed trades with P&L
cursor.execute("SELECT * FROM trades WHERE status='CLOSED'")
closed_trades = cursor.fetchall()

# Calculate stats
total_pnl = sum(t[6] for t in closed_trades) if closed_trades else 0
winning = sum(1 for t in closed_trades if t[6] > 0) if closed_trades else 0
losing = len(closed_trades) - winning if closed_trades else 0
win_rate = (winning / len(closed_trades) * 100) if closed_trades else 0

print(f"  Closed trades: {len(closed_trades) if closed_trades else 0}")
print(f"  Win rate: {win_rate:.1f}% ({winning}/{len(closed_trades) if closed_trades else 0})")
print(f"  Total P&L: ${total_pnl:.2f}")

# Check if any open trades hit stop-loss/take-profit
alerts = []
for trade in open_trades:
    symbol = trade[1]
    side = trade[2]
    entry = trade[3]
    current_price = prices.get(symbol, {}).get('price', 0)
    
    if current_price > 0:
        stop_loss = entry * 0.99 if side == 'BUY' else entry * 1.01
        take_profit = entry * 1.02 if side == 'BUY' else entry * 0.98
        
        if side == 'BUY':
            if current_price <= stop_loss:
                alerts.append(f"🚨 STOP LOSS: {symbol} @ ${current_price:,.2f}")
                # Update trade to closed
                pnl = (current_price - entry) * trade[5]
                pnl_pct = ((current_price - entry) / entry) * 100
                cursor.execute('''UPDATE trades SET status='CLOSED', exit_price=?, exit_time=?, profit_loss=?, profit_loss_pct=? WHERE id=?''',
                    (current_price, datetime.now().isoformat(), pnl, pnl_pct, trade[0]))
                conn.commit()
            elif current_price >= take_profit:
                alerts.append(f"✅ TAKE PROFIT: {symbol} @ ${current_price:,.2f}")
                pnl = (current_price - entry) * trade[5]
                pnl_pct = ((current_price - entry) / entry) * 100
                cursor.execute('''UPDATE trades SET status='CLOSED', exit_price=?, exit_time=?, profit_loss=?, profit_loss_pct=? WHERE id=?''',
                    (current_price, datetime.now().isoformat(), pnl, pnl_pct, trade[0]))
                conn.commit()

# Get updated open trades
cursor.execute("SELECT * FROM trades WHERE status='OPEN'")
open_trades = cursor.fetchall()

# Generate signals based on price action
print('\n[BOT] Generating trading signals...')
signals = {}
for symbol in symbols:
    if symbol in prices:
        price = prices[symbol]['price']
        change = prices[symbol]['change_24h']
        
        # Simple trend-based signal
        if change < -5:
            signal = 'SELL'
            confidence = 0.6
            reason = 'Downtrend confirmed'
        elif change > 2:
            signal = 'BUY'
            confidence = 0.7
            reason = 'Uptrend forming'
        else:
            signal = 'HOLD'
            confidence = 0.5
            reason = 'Sideways/consolidation'
        
        signals[symbol] = {
            'signal': signal,
            'confidence': confidence,
            'current_price': price,
            'reason': reason
        }
        print(f"  {symbol}: {signal} (confidence: {confidence}) - {reason}")

conn.close()

# Create daily report
report = {
    'timestamp': datetime.now().isoformat(),
    'status': 'PAPER_TRADING_ACTIVE',
    'market_summary': {
        'btc': prices.get('BTCUSDT', {}),
        'eth': prices.get('ETHUSDT', {}),
        'sol': prices.get('SOLUSDT', {})
    },
    'trading_stats': {
        'total_trades': len(closed_trades) if closed_trades else 0,
        'winning_trades': winning,
        'losing_trades': losing,
        'win_rate': win_rate,
        'total_pnl': round(total_pnl, 2),
        'open_trades': len(open_trades),
        'daily_loss_pct': round(abs(total_pnl) / 10, 2) if total_pnl < 0 else 0
    },
    'open_positions': [
        {
            'symbol': t[1],
            'entry': t[3],
            'current': prices.get(t[1], {}).get('price', t[3]),
            'qty': t[5]
        } for t in open_trades
    ],
    'signals': signals,
    'alerts': alerts if alerts else ['No alerts - monitoring market']
}

# Save report
with open('daily_trading_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print('\n[BOT] Daily report saved to daily_trading_report.json')
print(f"[BOT] Run complete at {datetime.now().strftime('%H:%M:%S')}")
