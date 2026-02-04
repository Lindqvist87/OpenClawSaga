#!/usr/bin/env python3
"""
Trading Bot Data Collection - One-shot execution
Fetches prices, checks signals, manages trades, updates reports
"""

import json
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

# Symbols to track
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
BINANCE_BASE = "https://api.binance.com"

def get_price(symbol):
    """Get current price from Binance"""
    try:
        response = requests.get(
            f"{BINANCE_BASE}/api/v3/ticker/price",
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
            f"{BINANCE_BASE}/api/v3/klines",
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
    if len(prices) < period:
        return sum(prices) / len(prices) if prices else 0
    return sum(prices[-period:]) / period

def calculate_ema(prices, period):
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
        return {'signal': 'HOLD', 'confidence': 0}
    
    closes = [c['close'] for c in candles]
    volumes = [c['volume'] for c in candles]
    
    sma_10 = calculate_sma(closes, 10)
    sma_20 = calculate_sma(closes, 20)
    sma_50 = calculate_sma(closes, 50)
    ema_12 = calculate_ema(closes, 12)
    ema_26 = calculate_ema(closes, 26)
    
    current_price = closes[-1]
    
    # Volume spike detection
    avg_volume = sum(volumes[-20:-1]) / 19 if len(volumes) >= 20 else sum(volumes) / len(volumes)
    volume_spike = volumes[-1] > avg_volume * 2 if volumes else False
    
    signal = 'HOLD'
    confidence = 0.0
    
    # Bullish signals
    if sma_10 > sma_20 and sma_20 > sma_50 and ema_12 > ema_26:
        signal = 'BUY'
        confidence = 0.8 if volume_spike else 0.6
    elif sma_10 < sma_20 and sma_20 < sma_50 and ema_12 < ema_26:
        signal = 'SELL'
        confidence = 0.6
    
    return {
        'signal': signal,
        'confidence': confidence,
        'current_price': current_price,
        'sma_10': sma_10,
        'sma_20': sma_20,
        'volume_spike': volume_spike
    }

def update_price_history(symbol, price):
    """Update price history in database"""
    conn = sqlite3.connect('projects/trading-bot/paper_trades.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            price REAL,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        INSERT INTO price_history (symbol, price, timestamp)
        VALUES (?, ?, ?)
    ''', (symbol, price, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_open_trades():
    """Get all open trades"""
    conn = sqlite3.connect('projects/trading-bot/paper_trades.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trades WHERE status = "OPEN"')
    trades = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'symbol', 'side', 'entry_price', 'exit_price', 'quantity', 
               'profit_loss', 'profit_loss_pct', 'entry_time', 'exit_time', 'status', 'strategy']
    return [dict(zip(columns, trade)) for trade in trades]

def close_trade(trade_id, exit_price, pnl, pnl_pct):
    """Close a trade in database"""
    conn = sqlite3.connect('projects/trading-bot/paper_trades.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE trades 
        SET exit_price=?, exit_time=?, status=?, profit_loss=?, profit_loss_pct=?
        WHERE id=?
    ''', (exit_price, datetime.now().isoformat(), 'CLOSED', pnl, pnl_pct, trade_id))
    conn.commit()
    conn.close()

def check_stop_loss_take_profit(open_trades, current_prices):
    """Check if any trades should be closed"""
    closed_trades = []
    
    for trade in open_trades:
        symbol = trade['symbol']
        if symbol not in current_prices:
            continue
            
        current_price = current_prices[symbol]
        entry_price = trade['entry_price']
        side = trade['side']
        quantity = trade['quantity']
        
        stop_loss = entry_price * 0.99 if side == 'BUY' else entry_price * 1.01
        take_profit = entry_price * 1.02 if side == 'BUY' else entry_price * 0.98
        
        if side == 'BUY':
            if current_price <= stop_loss:
                pnl = (current_price - entry_price) * quantity
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                close_trade(trade['id'], current_price, pnl, pnl_pct)
                closed_trades.append({
                    'id': trade['id'],
                    'symbol': symbol,
                    'reason': 'STOP_LOSS',
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
            elif current_price >= take_profit:
                pnl = (current_price - entry_price) * quantity
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                close_trade(trade['id'], current_price, pnl, pnl_pct)
                closed_trades.append({
                    'id': trade['id'],
                    'symbol': symbol,
                    'reason': 'TAKE_PROFIT',
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
    
    return closed_trades

def get_stats():
    """Get trading statistics"""
    conn = sqlite3.connect('projects/trading-bot/paper_trades.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM trades WHERE status = "CLOSED"')
    total_closed = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trades WHERE status = "CLOSED" AND profit_loss > 0')
    winning_trades = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(profit_loss) FROM trades WHERE status = "CLOSED"')
    total_pnl = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM trades WHERE status = "OPEN"')
    open_count = cursor.fetchone()[0]
    
    conn.close()
    
    win_rate = (winning_trades / total_closed * 100) if total_closed > 0 else 0
    
    return {
        'total_closed': total_closed,
        'winning_trades': winning_trades,
        'losing_trades': total_closed - winning_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'open_trades': open_count
    }

def update_daily_report(prices, signals, open_trades, closed_trades, stats):
    """Update daily trading report"""
    today = datetime.now().strftime('%Y-%m-%d')
    report_path = f'projects/trading-bot/reports/daily_trading_report_{today}.json'
    
    Path('projects/trading-bot/reports').mkdir(parents=True, exist_ok=True)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'prices': prices,
        'signals': signals,
        'open_trades_count': len(open_trades),
        'closed_trades': closed_trades,
        'stats': stats
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    print("="*60)
    print("TRADING BOT DATA COLLECTION")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 1. Fetch prices
    print("\n[PRICES] Fetching prices...")
    prices = {}
    for symbol in SYMBOLS:
        price = get_price(symbol)
        if price:
            prices[symbol] = price
            update_price_history(symbol, price)
            print(f"  {symbol}: ${price:,.2f}")
    
    # 2. Get open trades
    print("\n[TRADES] Open trades:")
    open_trades = get_open_trades()
    if open_trades:
        for trade in open_trades:
            print(f"  #{trade['id']} {trade['symbol']} {trade['side']} @ ${trade['entry_price']:,.2f}")
    else:
        print("  No open trades")
    
    # 3. Check signals
    print("\n[SIGNALS] Checking signals...")
    signals = {}
    for symbol in SYMBOLS:
        candles = get_klines(symbol)
        if candles:
            signal = generate_signal(candles)
            signals[symbol] = signal
            print(f"  {symbol}: {signal['signal']} (confidence: {signal['confidence']:.0%})")
    
    # 4. Manage open trades (stop-loss/take-profit)
    print("\n[RISK] Managing trades...")
    closed_trades = check_stop_loss_take_profit(open_trades, prices)
    if closed_trades:
        for trade in closed_trades:
            status = "WIN" if trade['pnl'] > 0 else "LOSS"
            print(f"  [{status}] Closed #{trade['id']} {trade['symbol']} via {trade['reason']}: ${trade['pnl']:.2f}")
    else:
        print("  No trades closed")
    
    # 5. Get stats
    stats = get_stats()
    
    # 6. Update report
    report = update_daily_report(prices, signals, open_trades, closed_trades, stats)
    
    # 7. Print summary
    print("\n" + "="*60)
    print("[SUMMARY]")
    print("="*60)
    print(f"Prices: BTC ${prices.get('BTCUSDT', 0):,.2f} | ETH ${prices.get('ETHUSDT', 0):,.2f} | SOL ${prices.get('SOLUSDT', 0):,.2f}")
    print(f"Open trades: {stats['open_trades']}")
    print(f"Total P&L: ${stats['total_pnl']:.2f}")
    print(f"Win rate: {stats['win_rate']:.1f}%")
    print(f"Report saved: {datetime.now().strftime('%Y-%m-%d')}")
    
    # Return summary for Discord
    return {
        'timestamp': datetime.now().isoformat(),
        'prices': prices,
        'stats': stats,
        'closed_trades': closed_trades,
        'signals': {s: signals[s]['signal'] for s in signals}
    }

if __name__ == "__main__":
    result = main()
    # Output JSON for external use
    print("\nJSON_OUTPUT_START")
    print(json.dumps(result))
    print("JSON_OUTPUT_END")
