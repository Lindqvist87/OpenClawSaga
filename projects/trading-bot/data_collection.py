#!/usr/bin/env python3
"""
Trading Bot - Data Collection Run
Fetch prices, check signals, manage trades, update reports
"""

import json
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

# Config
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
DB_PATH = Path('paper_trades.db')
REPORT_PATH = Path('daily_trading_report.json')
BINANCE_BASE = "https://api.binance.com"

def fetch_price(symbol):
    """Get current price from Binance"""
    try:
        response = requests.get(
            f"{BINANCE_BASE}/api/v3/ticker/24hr",
            params={"symbol": symbol},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return {
                'price': float(data['lastPrice']),
                'change_24h': float(data['priceChangePercent']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'volume': float(data['volume'])
            }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
    return None

def update_price_db(symbol, price_data):
    """Update price history in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            price REAL,
            timestamp TEXT
        )
    ''')
    
    cursor.execute('''
        INSERT INTO price_data (symbol, price, timestamp)
        VALUES (?, ?, ?)
    ''', (symbol, price_data['price'], datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def get_klines(symbol, interval='5m', limit=50):
    """Get candlestick data"""
    try:
        response = requests.get(
            f"{BINANCE_BASE}/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return [{
                'timestamp': item[0],
                'open': float(item[1]),
                'high': float(item[2]),
                'low': float(item[3]),
                'close': float(item[4]),
                'volume': float(item[5])
            } for item in data]
    except Exception as e:
        print(f"Error fetching klines for {symbol}: {e}")
    return []

def calculate_sma(prices, period):
    """Simple Moving Average"""
    if len(prices) < period:
        return sum(prices) / len(prices) if prices else 0
    return sum(prices[-period:]) / period

def generate_signal(candles):
    """Generate trading signal"""
    if len(candles) < 50:
        return {'signal': 'HOLD', 'confidence': 0}
    
    closes = [c['close'] for c in candles]
    
    sma_10 = calculate_sma(closes, 10)
    sma_20 = calculate_sma(closes, 20)
    sma_50 = calculate_sma(closes, 50)
    
    current_price = closes[-1]
    
    # Bullish signal
    if sma_10 > sma_20 and sma_20 > sma_50:
        return {'signal': 'BUY', 'confidence': 0.7, 'current_price': current_price}
    
    # Bearish signal
    elif sma_10 < sma_20 and sma_20 < sma_50:
        return {'signal': 'SELL', 'confidence': 0.6, 'current_price': current_price}
    
    return {'signal': 'HOLD', 'confidence': 0, 'current_price': current_price}

def get_open_trades():
    """Get all open trades from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, symbol, side, entry_price, quantity, stop_loss, take_profit
        FROM trades WHERE status = 'OPEN'
    ''')
    
    trades = cursor.fetchall()
    conn.close()
    return trades

def close_trade(trade_id, exit_price):
    """Close a trade with given exit price"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get trade details
    cursor.execute('SELECT entry_price, quantity, side FROM trades WHERE id = ?', (trade_id,))
    trade = cursor.fetchone()
    
    if trade:
        entry_price, quantity, side = trade
        
        # Calculate P&L
        if side == 'BUY':
            pnl = (exit_price - entry_price) * quantity
        else:
            pnl = (entry_price - exit_price) * quantity
        
        pnl_pct = (pnl / (entry_price * quantity)) * 100 if entry_price > 0 else 0
        
        cursor.execute('''
            UPDATE trades 
            SET exit_price = ?, exit_time = ?, status = 'CLOSED',
                profit_loss = ?, profit_loss_pct = ?
            WHERE id = ?
        ''', (exit_price, datetime.now().isoformat(), pnl, pnl_pct, trade_id))
        
        conn.commit()
        print(f"Closed trade {trade_id}: P&L ${pnl:.2f} ({pnl_pct:+.2f}%)")
    
    conn.close()

def check_and_manage_trades(current_prices):
    """Check open trades for stop-loss/take-profit triggers"""
    open_trades = get_open_trades()
    actions = []
    
    for trade in open_trades:
        trade_id, symbol, side, entry_price, quantity, stop_loss, take_profit = trade
        
        current_price = current_prices.get(symbol)
        if not current_price:
            continue
        
        # Default stop loss and take profit if not set (1% stop, 2% profit)
        if stop_loss is None:
            stop_loss = entry_price * 0.99 if side == 'BUY' else entry_price * 1.01
        if take_profit is None:
            take_profit = entry_price * 1.02 if side == 'BUY' else entry_price * 0.98
        
        # Check stop loss
        if side == 'BUY' and current_price <= stop_loss:
            close_trade(trade_id, current_price)
            actions.append(f"{symbol}: STOP LOSS triggered @ ${current_price:.2f}")
        elif side == 'SELL' and current_price >= stop_loss:
            close_trade(trade_id, current_price)
            actions.append(f"{symbol}: STOP LOSS triggered @ ${current_price:.2f}")
        
        # Check take profit
        elif side == 'BUY' and current_price >= take_profit:
            close_trade(trade_id, current_price)
            actions.append(f"{symbol}: TAKE PROFIT triggered @ ${current_price:.2f}")
        elif side == 'SELL' and current_price <= take_profit:
            close_trade(trade_id, current_price)
            actions.append(f"{symbol}: TAKE PROFIT triggered @ ${current_price:.2f}")
    
    return actions

def get_trading_stats():
    """Get trading statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all closed trades
    cursor.execute('''
        SELECT COUNT(*), SUM(profit_loss)
        FROM trades WHERE status = 'CLOSED'
    ''')
    total_trades, total_pnl = cursor.fetchone()
    total_trades = total_trades or 0
    total_pnl = total_pnl or 0
    
    # Get winning trades
    cursor.execute('''
        SELECT COUNT(*) FROM trades 
        WHERE status = 'CLOSED' AND profit_loss > 0
    ''')
    winning_trades = cursor.fetchone()[0] or 0
    
    # Get open trades count
    cursor.execute('SELECT COUNT(*) FROM trades WHERE status = "OPEN"')
    open_trades = cursor.fetchone()[0] or 0
    
    conn.close()
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': total_trades - winning_trades,
        'win_rate': round(win_rate, 2),
        'total_pnl': round(total_pnl, 2),
        'open_trades': open_trades
    }

def update_report(market_data, stats, alerts, signals):
    """Update daily trading report"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'status': 'PAPER_TRADING_ACTIVE',
        'market_summary': {
            'btc': market_data.get('BTCUSDT', {}),
            'eth': market_data.get('ETHUSDT', {}),
            'sol': market_data.get('SOLUSDT', {})
        },
        'trading_stats': stats,
        'signals': signals,
        'alerts': alerts
    }
    
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Updated report: {REPORT_PATH}")

def main():
    print("=" * 60)
    print("TRADING BOT - DATA COLLECTION RUN")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Fetch prices
    print("\n[1] Fetching prices from Binance...")
    market_data = {}
    for symbol in SYMBOLS:
        data = fetch_price(symbol)
        if data:
            market_data[symbol] = data
            print(f"  {symbol}: ${data['price']:,.2f} ({data['change_24h']:+.2f}%)")
            update_price_db(symbol, data)
    
    # 2. Check for trade signals
    print("\n[2] Checking trade signals...")
    signals = {}
    for symbol in SYMBOLS:
        candles = get_klines(symbol, interval='5m', limit=50)
        signal = generate_signal(candles)
        signals[symbol] = signal
        if signal['signal'] != 'HOLD':
            print(f"  {symbol}: {signal['signal']} (confidence: {signal['confidence']})")
    
    # 3. Manage open trades
    print("\n[3] Managing open trades...")
    prices_dict = {s: d['price'] for s, d in market_data.items()}
    actions = check_and_manage_trades(prices_dict)
    if actions:
        for action in actions:
            print(f"  {action}")
    else:
        print("  No trade actions taken")
    
    # 4. Get stats
    print("\n[4] Getting trading stats...")
    stats = get_trading_stats()
    print(f"  Total trades: {stats['total_trades']}")
    print(f"  Win rate: {stats['win_rate']}%")
    print(f"  Total P&L: ${stats['total_pnl']:.2f}")
    print(f"  Open trades: {stats['open_trades']}")
    
    # 5. Generate alerts
    print("\n[5] Generating alerts...")
    alerts = []
    for symbol, data in market_data.items():
        if abs(data['change_24h']) > 5:
            alerts.append(f"{symbol.replace('USDT', '')}: Significant move ({data['change_24h']:+.2f}%)")
    if alerts:
        for alert in alerts:
            print(f"  ALERT: {alert}")
    else:
        print("  No alerts")
    
    # 6. Update report
    print("\n[6] Updating daily report...")
    update_report(market_data, stats, alerts, signals)
    
    print("\n" + "=" * 60)
    print("DATA COLLECTION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
