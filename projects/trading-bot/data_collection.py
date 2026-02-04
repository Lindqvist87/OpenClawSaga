#!/usr/bin/env python3
"""
Trading Bot Data Collection - Single Cycle
Fetches prices, manages trades, updates reports
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
LOG_PATH = Path('trading_bot.log')
BINANCE_API = "https://api.binance.com"

def log(msg):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def fetch_price(symbol):
    """Fetch current price from Binance"""
    try:
        endpoint = f"{BINANCE_API}/api/v3/ticker/24hr"
        response = requests.get(endpoint, params={"symbol": symbol}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'symbol': symbol,
                'price': float(data['lastPrice']),
                'change_24h': float(data['priceChangePercent']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'volume': float(data['volume'])
            }
    except Exception as e:
        log(f"Error fetching {symbol}: {e}")
    return None

def get_klines(symbol, interval='5m', limit=50):
    """Get candlestick data for technical analysis"""
    try:
        endpoint = f"{BINANCE_API}/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        response = requests.get(endpoint, params=params, timeout=10)
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
        log(f"Error fetching klines for {symbol}: {e}")
    return []

def calculate_sma(prices, period):
    """Simple Moving Average"""
    if len(prices) < period:
        return sum(prices) / len(prices) if prices else 0
    return sum(prices[-period:]) / period

def generate_signal(candles):
    """Generate trading signal from candle data"""
    if len(candles) < 50:
        return {'signal': 'HOLD', 'confidence': 0, 'reason': 'Insufficient data'}
    
    closes = [c['close'] for c in candles]
    volumes = [c['volume'] for c in candles]
    
    sma_10 = calculate_sma(closes, 10)
    sma_20 = calculate_sma(closes, 20)
    sma_50 = calculate_sma(closes, 50)
    current_price = closes[-1]
    
    # Volume spike detection
    avg_volume = sum(volumes[-20:-1]) / 19 if len(volumes) >= 20 else 0
    volume_spike = volumes[-1] > (avg_volume * 2.0) if volumes else False
    
    # Generate signal
    signal = 'HOLD'
    confidence = 0.0
    reason = 'No clear signal'
    
    # Bullish signals
    if sma_10 > sma_20 and current_price > sma_50:
        if volume_spike:
            signal = 'BUY'
            reason = 'Uptrend with volume spike'
            confidence = 0.8
        else:
            signal = 'BUY'
            reason = 'Uptrend confirmed'
            confidence = 0.6
    
    # Bearish signals
    elif sma_10 < sma_20 and current_price < sma_50:
        signal = 'SELL'
        reason = 'Downtrend confirmed'
        confidence = 0.5
    
    return {
        'signal': signal,
        'confidence': confidence,
        'reason': reason,
        'current_price': current_price,
        'sma_10': sma_10,
        'sma_20': sma_20,
        'sma_50': sma_50
    }

def get_open_trades():
    """Get all open trades from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades WHERE status = 'OPEN'")
    columns = [description[0] for description in cursor.description]
    trades = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return trades

def close_trade(trade_id, exit_price):
    """Close a trade and calculate P&L"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get trade details
    cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    columns = [description[0] for description in cursor.description]
    trade = dict(zip(columns, row))
    
    # Calculate P&L
    if trade['side'] == 'BUY':
        pnl = (exit_price - trade['entry_price']) * trade['quantity']
        pnl_pct = ((exit_price - trade['entry_price']) / trade['entry_price']) * 100
    else:
        pnl = (trade['entry_price'] - exit_price) * trade['quantity']
        pnl_pct = ((trade['entry_price'] - exit_price) / trade['entry_price']) * 100
    
    # Update trade
    exit_time = datetime.now().isoformat()
    cursor.execute('''
        UPDATE trades 
        SET exit_price = ?, exit_time = ?, status = 'CLOSED', 
            profit_loss = ?, profit_loss_pct = ?
        WHERE id = ?
    ''', (exit_price, exit_time, pnl, pnl_pct, trade_id))
    
    conn.commit()
    conn.close()
    
    log(f"CLOSED trade {trade_id}: P&L = ${pnl:.2f} ({pnl_pct:+.2f}%)")
    return {'pnl': pnl, 'pnl_pct': pnl_pct}

def manage_open_trades(prices):
    """Check and manage open trades (stop-loss/take-profit)"""
    open_trades = get_open_trades()
    if not open_trades:
        return []
    
    closed_trades = []
    stop_pct = 0.01  # 1% stop loss
    profit_pct = 0.02  # 2% take profit
    
    for trade in open_trades:
        symbol = trade['symbol']
        current_price = prices.get(symbol, {}).get('price')
        
        if not current_price:
            continue
        
        entry = trade['entry_price']
        side = trade['side']
        
        if side == 'BUY':
            stop_loss = entry * (1 - stop_pct)
            take_profit = entry * (1 + profit_pct)
            
            if current_price <= stop_loss:
                log(f"STOP LOSS triggered for {symbol} at ${current_price:.2f}")
                result = close_trade(trade['id'], current_price)
                if result:
                    closed_trades.append({'symbol': symbol, 'reason': 'STOP_LOSS', **result})
            elif current_price >= take_profit:
                log(f"TAKE PROFIT triggered for {symbol} at ${current_price:.2f}")
                result = close_trade(trade['id'], current_price)
                if result:
                    closed_trades.append({'symbol': symbol, 'reason': 'TAKE_PROFIT', **result})
        
        else:  # SELL
            stop_loss = entry * (1 + stop_pct)
            take_profit = entry * (1 - profit_pct)
            
            if current_price >= stop_loss:
                log(f"STOP LOSS triggered for {symbol} at ${current_price:.2f}")
                result = close_trade(trade['id'], current_price)
                if result:
                    closed_trades.append({'symbol': symbol, 'reason': 'STOP_LOSS', **result})
            elif current_price <= take_profit:
                log(f"TAKE PROFIT triggered for {symbol} at ${current_price:.2f}")
                result = close_trade(trade['id'], current_price)
                if result:
                    closed_trades.append({'symbol': symbol, 'reason': 'TAKE_PROFIT', **result})
    
    return closed_trades

def open_new_trade(symbol, side, price, quantity):
    """Open a new paper trade"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get next ID
    cursor.execute("SELECT MAX(id) FROM trades")
    max_id = cursor.fetchone()[0]
    trade_id = (max_id or 0) + 1
    
    entry_time = datetime.now().isoformat()
    stop_loss = price * 0.99 if side == 'BUY' else price * 1.01
    take_profit = price * 1.02 if side == 'BUY' else price * 0.98
    
    cursor.execute('''
        INSERT INTO trades (id, symbol, side, entry_price, quantity, entry_time, status, strategy, stop_loss, take_profit)
        VALUES (?, ?, ?, ?, ?, ?, 'OPEN', 'micro_scalp', ?, ?)
    ''', (trade_id, symbol, side, price, quantity, entry_time, stop_loss, take_profit))
    
    conn.commit()
    conn.close()
    
    log(f"OPENED {side} trade: {symbol} @ ${price:.2f} x {quantity}")
    return trade_id

def check_new_signals(prices, signals):
    """Check for new trading opportunities"""
    open_trades = get_open_trades()
    open_symbols = [t['symbol'] for t in open_trades]
    
    new_trades = []
    
    for symbol in SYMBOLS:
        if symbol in open_symbols:
            continue
        
        signal_data = signals.get(symbol, {})
        if signal_data.get('signal') == 'BUY' and signal_data.get('confidence', 0) >= 0.6:
            price = signal_data.get('current_price')
            if price:
                # Fixed position size: $20 per trade
                position_value = 20.0
                quantity = round(position_value / price, 6)
                trade_id = open_new_trade(symbol, 'BUY', price, quantity)
                new_trades.append({'id': trade_id, 'symbol': symbol, 'price': price, 'quantity': quantity})
    
    return new_trades

def get_trading_stats():
    """Get overall trading statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all closed trades
    cursor.execute("SELECT * FROM trades WHERE status = 'CLOSED'")
    columns = [description[0] for description in cursor.description]
    closed_trades = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Get open trades
    cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'OPEN'")
    open_count = cursor.fetchone()[0]
    
    conn.close()
    
    if not closed_trades:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'open_trades': open_count
        }
    
    winning = sum(1 for t in closed_trades if t.get('profit_loss', 0) > 0)
    losing = sum(1 for t in closed_trades if t.get('profit_loss', 0) <= 0)
    total_pnl = sum(t.get('profit_loss', 0) for t in closed_trades)
    
    return {
        'total_trades': len(closed_trades),
        'winning_trades': winning,
        'losing_trades': losing,
        'win_rate': (winning / len(closed_trades)) * 100,
        'total_pnl': total_pnl,
        'open_trades': open_count
    }

def update_price_db(symbol, price_data):
    """Update price data in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if price_data table exists with full schema
    cursor.execute("PRAGMA table_info(price_data)")
    columns = [c[1] for c in cursor.fetchall()]
    
    if not columns:
        # Create new table with full schema
        cursor.execute('''
            CREATE TABLE price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                price REAL,
                change_24h REAL,
                high_24h REAL,
                low_24h REAL,
                volume REAL,
                timestamp TEXT
            )
        ''')
    elif 'change_24h' not in columns:
        # Drop and recreate with full schema
        cursor.execute("DROP TABLE IF EXISTS price_data")
        cursor.execute('''
            CREATE TABLE price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                price REAL,
                change_24h REAL,
                high_24h REAL,
                low_24h REAL,
                volume REAL,
                timestamp TEXT
            )
        ''')
    
    timestamp = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO price_data (symbol, price, change_24h, high_24h, low_24h, volume, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (symbol, price_data['price'], price_data['change_24h'], 
          price_data['high_24h'], price_data['low_24h'], price_data['volume'], timestamp))
    
    conn.commit()
    conn.close()

def save_report(report):
    """Save daily trading report"""
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

def main():
    log("=" * 60)
    log("TRADING BOT DATA COLLECTION CYCLE")
    log("=" * 60)
    
    # 1. Fetch prices from Binance
    log("Step 1: Fetching prices from Binance...")
    prices = {}
    market_summary = {}
    
    for symbol in SYMBOLS:
        data = fetch_price(symbol)
        if data:
            prices[symbol] = data
            market_summary[symbol.lower().replace('usdt', '')] = {
                'price': data['price'],
                'change_24h': data['change_24h'],
                'high_24h': data['high_24h'],
                'low_24h': data['low_24h'],
                'volume': data['volume']
            }
            log(f"  {symbol}: ${data['price']:,.2f} ({data['change_24h']:+.2f}%)")
            
            # 2. Update price database
            update_price_db(symbol, data)
    
    if not prices:
        log("ERROR: Failed to fetch any prices")
        return
    
    log("Step 2: Database updated with price data")
    
    # Generate signals
    log("Step 3: Generating trading signals...")
    signals = {}
    for symbol in SYMBOLS:
        candles = get_klines(symbol, interval='5m', limit=50)
        signal = generate_signal(candles)
        signals[symbol] = signal
        log(f"  {symbol}: {signal['signal']} (confidence: {signal['confidence']:.1f}) - {signal['reason']}")
    
    # 4. Manage open trades
    log("Step 4: Managing open trades...")
    closed_trades = manage_open_trades(prices)
    if closed_trades:
        for t in closed_trades:
            log(f"  Closed {t['symbol']}: {t['reason']} | P&L: ${t['pnl']:.2f}")
    else:
        log("  No trades closed")
    
    # 5. Check for new signals
    log("Step 5: Checking for new trade signals...")
    new_trades = check_new_signals(prices, signals)
    if new_trades:
        for t in new_trades:
            log(f"  Opened {t['symbol']} @ ${t['price']:.2f}")
    else:
        log("  No new trades opened")
    
    # Get stats
    stats = get_trading_stats()
    log(f"Step 6: Trading stats - Trades: {stats['total_trades']}, Win Rate: {stats['win_rate']:.1f}%, P&L: ${stats['total_pnl']:+.2f}")
    
    # 5. Update daily report
    log("Step 7: Updating daily_trading_report.json...")
    report = {
        'timestamp': datetime.now().isoformat(),
        'status': 'PAPER_TRADING_ACTIVE',
        'market_summary': market_summary,
        'trading_stats': stats,
        'signals': {s: {'signal': signals[s]['signal'], 'confidence': signals[s]['confidence'], 'current_price': signals[s]['current_price']} for s in signals},
        'closed_trades': closed_trades,
        'new_trades': new_trades,
        'alerts': []
    }
    
    # Add alerts for significant moves
    for symbol, data in prices.items():
        if abs(data['change_24h']) > 5:
            report['alerts'].append(f"{symbol.replace('USDT', '')}: Significant move ({data['change_24h']:+.2f}%)")
    
    save_report(report)
    log("Report saved successfully")
    
    # Summary
    log("=" * 60)
    log("CYCLE COMPLETE")
    log(f"Open trades: {stats['open_trades']}")
    log(f"Total P&L: ${stats['total_pnl']:+.2f}")
    log(f"Win rate: {stats['win_rate']:.1f}%")
    log("=" * 60)
    
    return report

if __name__ == "__main__":
    main()
