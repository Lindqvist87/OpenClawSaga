#!/usr/bin/env python3
"""
Trading Bot Data Collection - Single Run
Fetches prices, checks signals, manages trades, updates reports
"""

import json
import sqlite3
import os
from datetime import datetime
from pathlib import Path
import requests

# Symbols to track
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
BINANCE_URL = "https://api.binance.com"

def get_price(symbol):
    """Get current price from Binance"""
    try:
        response = requests.get(
            f"{BINANCE_URL}/api/v3/ticker/price",
            params={"symbol": symbol},
            timeout=10
        )
        if response.status_code == 200:
            return float(response.json()['price'])
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
    return None

def get_klines(symbol, interval="5m", limit=50):
    """Get candlestick data"""
    try:
        response = requests.get(
            f"{BINANCE_URL}/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            candles = []
            for item in data:
                candles.append({
                    'timestamp': item[0],
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5])
                })
            return candles
    except Exception as e:
        print(f"Error fetching klines for {symbol}: {e}")
    return []

def calculate_sma(prices, period):
    """Simple Moving Average"""
    if len(prices) < period:
        return sum(prices) / len(prices) if prices else 0
    return sum(prices[-period:]) / period

def calculate_ema(prices, period):
    """Exponential Moving Average"""
    if len(prices) < period:
        return sum(prices) / len(prices) if prices else 0
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def generate_signal(candles):
    """Generate trading signal"""
    if len(candles) < 50:
        return {'signal': 'HOLD', 'reason': 'Insufficient data', 'confidence': 0}
    
    closes = [c['close'] for c in candles]
    volumes = [c['volume'] for c in candles]
    
    sma_10 = calculate_sma(closes, 10)
    sma_20 = calculate_sma(closes, 20)
    sma_50 = calculate_sma(closes, 50)
    ema_12 = calculate_ema(closes, 12)
    ema_26 = calculate_ema(closes, 26)
    
    current_price = closes[-1]
    
    # Volume spike detection
    if len(volumes) >= 20:
        avg_volume = sum(volumes[-20:-1]) / 19
        current_volume = volumes[-1]
        volume_spike = current_volume > (avg_volume * 2.0)
    else:
        volume_spike = False
    
    # Generate signals
    signal = 'HOLD'
    reason = 'No clear signal'
    confidence = 0.0
    
    # Bullish signals
    if sma_10 > sma_20 and sma_20 > sma_50:
        if ema_12 > ema_26:
            if volume_spike:
                signal = 'BUY'
                reason = 'Strong uptrend with volume spike'
                confidence = 0.8
            else:
                signal = 'BUY'
                reason = 'Uptrend confirmed'
                confidence = 0.6
    
    # Bearish signals
    elif sma_10 < sma_20 and sma_20 < sma_50:
        if ema_12 < ema_26:
            signal = 'SELL'
            reason = 'Downtrend confirmed'
            confidence = 0.6
    
    return {
        'signal': signal,
        'reason': reason,
        'confidence': confidence,
        'current_price': current_price,
        'sma_10': sma_10,
        'sma_20': sma_20,
        'sma_50': sma_50,
        'volume_spike': volume_spike
    }

def setup_database():
    """Setup SQLite database"""
    db_path = Path('projects/trading-bot/paper_trades.db')
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            side TEXT,
            entry_price REAL,
            exit_price REAL,
            quantity REAL,
            profit_loss REAL,
            profit_loss_pct REAL,
            entry_time TEXT,
            exit_time TEXT,
            status TEXT,
            strategy TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            price REAL,
            timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    return db_path

def get_open_trades(db_path):
    """Get all open trades"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades WHERE status = 'OPEN'")
    trades = cursor.fetchall()
    conn.close()
    
    # Convert to dict
    columns = ['id', 'symbol', 'side', 'entry_price', 'exit_price', 'quantity', 
               'profit_loss', 'profit_loss_pct', 'entry_time', 'exit_time', 'status', 'strategy']
    return [dict(zip(columns, trade)) for trade in trades]

def close_trade(db_path, trade_id, exit_price):
    """Close a trade with P&L calculation"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get trade details
    cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
    trade = cursor.fetchone()
    
    if trade:
        entry_price = trade[3]
        quantity = trade[5]
        side = trade[2]
        
        if side == 'BUY':
            pnl = (exit_price - entry_price) * quantity
        else:
            pnl = (entry_price - exit_price) * quantity
        
        pnl_pct = (pnl / (entry_price * quantity)) * 100 if entry_price > 0 else 0
        exit_time = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE trades 
            SET exit_price = ?, exit_time = ?, status = 'CLOSED', 
                profit_loss = ?, profit_loss_pct = ?
            WHERE id = ?
        ''', (exit_price, exit_time, pnl, pnl_pct, trade_id))
        
        conn.commit()
        print(f"Closed trade {trade_id}: P&L = ${pnl:.2f} ({pnl_pct:+.2f}%)")
    
    conn.close()

def open_trade(db_path, symbol, side, price, quantity):
    """Open a new trade"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get next ID
    cursor.execute("SELECT MAX(id) FROM trades")
    result = cursor.fetchone()
    next_id = (result[0] or 0) + 1
    
    entry_time = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO trades (id, symbol, side, entry_price, quantity, entry_time, status, strategy)
        VALUES (?, ?, ?, ?, ?, ?, 'OPEN', 'micro_scalp')
    ''', (next_id, symbol, side, price, quantity, entry_time))
    
    conn.commit()
    conn.close()
    
    print(f"Opened {side} trade: {symbol} @ ${price:.2f} x {quantity}")
    return next_id

def save_price_data(db_path, symbol, price):
    """Save price data to database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("INSERT INTO price_data (symbol, price, timestamp) VALUES (?, ?, ?)",
                   (symbol, price, timestamp))
    conn.commit()
    conn.close()

def check_manage_trades(db_path, prices):
    """Check open trades and manage stop-loss/take-profit"""
    open_trades = get_open_trades(db_path)
    closed_trades = []
    
    for trade in open_trades:
        symbol = trade['symbol']
        current_price = prices.get(symbol)
        
        if not current_price:
            continue
        
        entry_price = trade['entry_price']
        side = trade['side']
        
        # Calculate stop loss (1%) and take profit (2%)
        if side == 'BUY':
            stop_loss = entry_price * 0.99
            take_profit = entry_price * 1.02
            
            if current_price <= stop_loss:
                close_trade(db_path, trade['id'], current_price)
                closed_trades.append({**trade, 'exit_price': current_price, 'reason': 'STOP_LOSS'})
            elif current_price >= take_profit:
                close_trade(db_path, trade['id'], current_price)
                closed_trades.append({**trade, 'exit_price': current_price, 'reason': 'TAKE_PROFIT'})
        
        else:  # SELL
            stop_loss = entry_price * 1.01
            take_profit = entry_price * 0.98
            
            if current_price >= stop_loss:
                close_trade(db_path, trade['id'], current_price)
                closed_trades.append({**trade, 'exit_price': current_price, 'reason': 'STOP_LOSS'})
            elif current_price <= take_profit:
                close_trade(db_path, trade['id'], current_price)
                closed_trades.append({**trade, 'exit_price': current_price, 'reason': 'TAKE_PROFIT'})
    
    return closed_trades

def get_portfolio_value(db_path, prices):
    """Calculate current portfolio value"""
    open_trades = get_open_trades(db_path)
    value = 1000.0  # Initial balance
    
    for trade in open_trades:
        symbol = trade['symbol']
        current_price = prices.get(symbol, trade['entry_price'])
        value += trade['quantity'] * current_price
    
    return value

def get_stats(db_path):
    """Get trading statistics"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED'")
    total_trades = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED' AND profit_loss > 0")
    winning_trades = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'OPEN'")
    open_trades = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(profit_loss) FROM trades WHERE status = 'CLOSED'")
    total_pnl = cursor.fetchone()[0] or 0
    
    conn.close()
    
    losing_trades = total_trades - winning_trades
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'open_trades': open_trades
    }

def update_daily_report(db_path, prices, signals, closed_trades, new_trade):
    """Update daily trading report"""
    report_path = Path('projects/trading-bot/daily_trading_report.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    stats = get_stats(db_path)
    portfolio_value = get_portfolio_value(db_path, prices)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'prices': prices,
        'signals': signals,
        'portfolio_value': portfolio_value,
        'stats': stats,
        'closed_trades': closed_trades,
        'new_trade': new_trade
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Updated daily report: {report_path}")
    return report

def main():
    print("="*60)
    print("MICRO-SCALP BOT - DATA COLLECTION")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Setup database
    db_path = setup_database()
    print(f"Database: {db_path}")
    
    # 2. Fetch prices
    print("\n[1/6] Fetching prices from Binance...")
    prices = {}
    for symbol in SYMBOLS:
        price = get_price(symbol)
        if price:
            prices[symbol] = price
            print(f"  {symbol}: ${price:,.2f}")
            save_price_data(db_path, symbol, price)
    
    # 3. Generate signals
    print("\n[2/6] Generating trading signals...")
    signals = {}
    for symbol in SYMBOLS:
        candles = get_klines(symbol, interval='5m', limit=50)
        if candles:
            signal = generate_signal(candles)
            signals[symbol] = signal
            print(f"  {symbol}: {signal['signal']} ({signal['reason']}, confidence: {signal['confidence']})")
    
    # 4. Manage open trades (stop-loss/take-profit)
    print("\n[3/6] Managing open trades...")
    closed_trades = check_manage_trades(db_path, prices)
    if closed_trades:
        for trade in closed_trades:
            print(f"  Closed: {trade['symbol']} - {trade['reason']}")
    else:
        print("  No trades closed")
    
    # 5. Check for new signals and open trades
    print("\n[4/6] Checking for new trade signals...")
    new_trade = None
    open_trades = get_open_trades(db_path)
    open_symbols = [t['symbol'] for t in open_trades]
    
    for symbol in SYMBOLS:
        if symbol in open_symbols:
            print(f"  {symbol}: Already have open trade")
            continue
        
        signal = signals.get(symbol)
        if signal and signal['signal'] == 'BUY' and signal['confidence'] >= 0.6:
            current_price = prices.get(symbol)
            if current_price:
                # Calculate position size (2% of portfolio)
                portfolio_value = get_portfolio_value(db_path, prices)
                position_value = portfolio_value * 0.02
                quantity = position_value / current_price
                
                trade_id = open_trade(db_path, symbol, 'BUY', current_price, quantity)
                new_trade = {
                    'id': trade_id,
                    'symbol': symbol,
                    'side': 'BUY',
                    'price': current_price,
                    'quantity': quantity
                }
                break  # Only open one trade per cycle
    
    if not new_trade:
        print("  No new trades opened")
    
    # 6. Update daily report
    print("\n[5/6] Updating daily trading report...")
    report = update_daily_report(db_path, prices, signals, closed_trades, new_trade)
    
    # 7. Print summary
    print("\n[6/6] Summary:")
    print("-"*60)
    stats = report['stats']
    print(f"Portfolio Value: ${report['portfolio_value']:,.2f}")
    print(f"Open Trades: {stats['open_trades']}")
    print(f"Total Closed Trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate']:.1f}%")
    print(f"Total P&L: ${stats['total_pnl']:+.2f}")
    print("-"*60)
    
    # Return report for Discord message
    return report

if __name__ == "__main__":
    report = main()
    
    # Print report as JSON for Discord bot to pick up
    print("\nREPORT_JSON_START")
    print(json.dumps(report))
    print("REPORT_JSON_END")
