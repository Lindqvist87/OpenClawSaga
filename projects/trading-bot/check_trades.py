import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('paper_trades.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM trades WHERE status = 'OPEN'")
open_trades = cursor.fetchall()

current_prices = {
    'BTCUSDT': 70810.0,
    'ETHUSDT': 2102.81,
    'SOLUSDT': 91.53
}

print('=== OPEN TRADES STATUS ===')
total_pnl = 0
for trade in open_trades:
    id, symbol, side, entry, exit, qty, pnl, pnl_pct, entry_time, exit_time, status, strategy, sl, tp = trade
    current = current_prices.get(symbol, entry)
    unrealized_pnl = (current - entry) * qty
    unrealized_pct = ((current - entry) / entry) * 100
    total_pnl += unrealized_pnl
    print(f'{symbol}: BUY @{entry:.2f} | Current: {current:.2f} | P&L: ${unrealized_pnl:.2f} ({unrealized_pct:.2f}%)')

print(f'\nTotal Unrealized P&L: ${total_pnl:.2f} USD')
conn.close()
