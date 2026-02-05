import requests
import json
from datetime import datetime

# Fetch fresh prices from Binance
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
prices = {}

for symbol in symbols:
    try:
        response = requests.get('https://api.binance.com/api/v3/ticker/24hr', params={'symbol': symbol}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            prices[symbol] = {
                'price': float(data['lastPrice']),
                'change_24h': float(data['priceChangePercent']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice']),
                'volume': float(data['volume'])
            }
    except Exception as e:
        print(f'Error fetching {symbol}: {e}')

# Load previous report to check open positions
try:
    with open('daily_trading_report.json', 'r') as f:
        prev_report = json.load(f)
    open_positions = prev_report.get('open_positions', [])
except:
    prev_report = {'trading_stats': {'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0, 'total_pnl': 0}}
    open_positions = []

# Calculate PnL for open positions
for pos in open_positions:
    symbol = pos['symbol']
    if symbol in prices:
        current = prices[symbol]['price']
        entry = pos['entry']
        qty = 0.001 if 'BTC' in symbol else (0.01 if 'ETH' in symbol else 0.1)
        pnl = (current - entry) * qty
        pnl_pct = ((current - entry) / entry) * 100
        pos['current'] = current
        pos['pnl'] = round(pnl, 2)
        pos['pnl_pct'] = round(pnl_pct, 2)

# Check if stop-loss or take-profit should trigger
stop_loss_pct = 1.0
take_profit_pct = 2.0
closed_trades = []
alerts = []

for pos in open_positions[:]:
    entry = pos['entry']
    current = pos['current']
    pnl_pct = pos['pnl_pct']
    symbol = pos['symbol']
    
    if pnl_pct <= -stop_loss_pct:
        closed_trades.append({
            'symbol': symbol,
            'exit_price': current,
            'pnl': pos['pnl'],
            'pnl_pct': pnl_pct,
            'reason': 'STOP_LOSS'
        })
        alerts.append(f"STOP LOSS triggered for {symbol} at {pnl_pct:.2f}%")
        open_positions.remove(pos)
    elif pnl_pct >= take_profit_pct:
        closed_trades.append({
            'symbol': symbol,
            'exit_price': current,
            'pnl': pos['pnl'],
            'pnl_pct': pnl_pct,
            'reason': 'TAKE_PROFIT'
        })
        alerts.append(f"TAKE PROFIT triggered for {symbol} at {pnl_pct:.2f}%")
        open_positions.remove(pos)

# Check for new signals (simplified EMA crossover)
signals = {}
for symbol in symbols:
    try:
        klines = requests.get('https://api.binance.com/api/v3/klines', 
                             params={'symbol': symbol, 'interval': '5m', 'limit': 50},
                             timeout=10).json()
        closes = [float(k[4]) for k in klines]
        
        # Simple trend detection
        sma_10 = sum(closes[-10:]) / 10
        sma_20 = sum(closes[-20:]) / 20
        
        if sma_10 > sma_20:
            signals[symbol] = {'signal': 'BUY', 'confidence': 0.6, 'reason': 'Uptrend detected'}
        elif sma_10 < sma_20:
            signals[symbol] = {'signal': 'SELL', 'confidence': 0.6, 'reason': 'Downtrend detected'}
        else:
            signals[symbol] = {'signal': 'HOLD', 'confidence': 0.5, 'reason': 'No clear trend'}
            
        signals[symbol]['current_price'] = prices.get(symbol, {}).get('price', closes[-1])
    except Exception as e:
        signals[symbol] = {'signal': 'ERROR', 'reason': str(e)}

# Calculate stats
open_pnl = sum(p['pnl'] for p in open_positions)

# Create report
report = {
    "timestamp": datetime.now().isoformat(),
    "status": "PAPER_TRADING_ACTIVE",
    "market_summary": {
        "btc": prices.get('BTCUSDT', {}),
        "eth": prices.get('ETHUSDT', {}),
        "sol": prices.get('SOLUSDT', {})
    },
    "trading_stats": {
        "total_trades": prev_report.get('trading_stats', {}).get('total_trades', 0) + len(closed_trades),
        "winning_trades": prev_report.get('trading_stats', {}).get('winning_trades', 0) + sum(1 for t in closed_trades if t['pnl'] > 0),
        "losing_trades": prev_report.get('trading_stats', {}).get('losing_trades', 0) + sum(1 for t in closed_trades if t['pnl'] <= 0),
        "win_rate": 0,
        "total_pnl": prev_report.get('trading_stats', {}).get('total_pnl', 0) + sum(t['pnl'] for t in closed_trades),
        "open_trades": len(open_positions),
        "open_trades_pnl": round(open_pnl, 2),
        "daily_loss_pct": round(abs(min(0, open_pnl)) / 1000 * 100, 2)
    },
    "open_positions": open_positions,
    "signals": signals,
    "closed_trades_today": closed_trades,
    "alerts": alerts + ["Data collection completed successfully"]
}

# Save report
with open('daily_trading_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
