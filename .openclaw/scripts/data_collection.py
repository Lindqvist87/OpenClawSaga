#!/usr/bin/env python3
"""
Windows-compatible Data Collection for Trading Bot
Replaces shell commands with Python-only implementation
"""

import sys
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths (Windows-compatible)
WORKSPACE = Path("C:/Users/Hejhej/.openclaw/workspace")
TRADING_DIR = WORKSPACE / "projects" / "trading-bot"
DB_PATH = TRADING_DIR / "paper_trades.db"
REPORT_PATH = TRADING_DIR / "daily_trading_report.json"
LOG_PATH = TRADING_DIR / "trading_bot.log"

class BinanceAPI:
    """Binance API client using only standard library"""
    
    BASE_URL = "https://api.binance.com"
    
    @staticmethod
    def fetch_price(symbol):
        """Fetch current price for symbol"""
        try:
            url = f"{BinanceAPI.BASE_URL}/api/v3/ticker/24hr?symbol={symbol}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                return {
                    'price': float(data['lastPrice']),
                    'change_24h': float(data['priceChangePercent']),
                    'high_24h': float(data['highPrice']),
                    'low_24h': float(data['lowPrice']),
                    'volume': float(data['volume'])
                }
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None
    
    @staticmethod
    def fetch_klines(symbol, interval="5m", limit=50):
        """Fetch candlestick data"""
        try:
            url = f"{BinanceAPI.BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
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
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return []


def update_report(symbols_data):
    """Update daily trading report"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'status': 'PAPER_TRADING_ACTIVE',
        'market_summary': symbols_data,
        'alerts': generate_alerts(symbols_data)
    }
    
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report updated: {REPORT_PATH}")


def generate_alerts(symbols_data):
    """Generate market alerts"""
    alerts = []
    
    for symbol, data in symbols_data.items():
        if data.get('change_24h', 0) < -5:
            alerts.append(f"{symbol}: Heavy drop ({data['change_24h']:.2f}%)")
        elif data.get('change_24h', 0) > 5:
            alerts.append(f"{symbol}: Strong pump ({data['change_24h']:.2f}%)")
    
    if not alerts:
        alerts.append("Market stable - no major movements")
    
    return alerts


def check_open_trades():
    """Check and manage open trades"""
    if not DB_PATH.exists():
        logger.info("No database found, skipping trade check")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, symbol, side, entry_price, quantity FROM trades WHERE status = 'OPEN'")
    open_trades = cursor.fetchall()
    
    logger.info(f"Open trades: {len(open_trades)}")
    
    for trade in open_trades:
        trade_id, symbol, side, entry_price, quantity = trade
        current_data = BinanceAPI.fetch_price(symbol)
        
        if not current_data:
            continue
        
        current_price = current_data['price']
        
        # Check stop loss (1%) and take profit (2%)
        if side == 'BUY':
            stop_loss = entry_price * 0.99
            take_profit = entry_price * 1.02
            
            if current_price <= stop_loss:
                logger.info(f"STOP LOSS: {symbol} at ${current_price:.2f}")
                close_trade(conn, trade_id, current_price)
            elif current_price >= take_profit:
                logger.info(f"TAKE PROFIT: {symbol} at ${current_price:.2f}")
                close_trade(conn, trade_id, current_price)
    
    conn.close()


def close_trade(conn, trade_id, exit_price):
    """Close a trade in the database"""
    cursor = conn.cursor()
    cursor.execute("SELECT entry_price, quantity, side FROM trades WHERE id = ?", (trade_id,))
    trade = cursor.fetchone()
    
    if not trade:
        return
    
    entry_price, quantity, side = trade
    
    if side == 'BUY':
        pnl = (exit_price - entry_price) * quantity
    else:
        pnl = (entry_price - exit_price) * quantity
    
    pnl_pct = (pnl / (entry_price * quantity)) * 100
    
    cursor.execute('''
        UPDATE trades 
        SET exit_price = ?, exit_time = ?, status = 'CLOSED', 
            profit_loss = ?, profit_loss_pct = ?
        WHERE id = ?
    ''', (exit_price, datetime.now().isoformat(), pnl, pnl_pct, trade_id))
    
    conn.commit()
    logger.info(f"Closed trade {trade_id}: P&L ${pnl:.2f} ({pnl_pct:.2f}%)")


def main():
    """Main data collection loop"""
    logger.info("="*60)
    logger.info("📊 TRADING BOT DATA COLLECTION (Windows)")
    logger.info("="*60)
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    symbols_data = {}
    
    # Fetch prices
    for symbol in symbols:
        data = BinanceAPI.fetch_price(symbol)
        if data:
            symbols_data[symbol.lower().replace('usdt', '')] = data
            logger.info(f"{symbol}: ${data['price']:.2f} ({data['change_24h']:+.2f}%)")
    
    # Check open trades
    check_open_trades()
    
    # Update report
    update_report(symbols_data)
    
    logger.info("="*60)
    logger.info("✅ Data collection complete")
    logger.info("="*60)


if __name__ == "__main__":
    main()
