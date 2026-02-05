#!/usr/bin/env python3
"""
Fix micro_scalp_bot.py - Add stop_loss and take_profit to Trade class and INSERT
"""

import re

file_path = r"C:\Users\Hejhej\.openclaw\workspace\projects\trading-bot\micro_scalp_bot.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add stop_loss and take_profit to Trade class
old_trade = '''    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: float = 0.0
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    entry_time: str = ""
    exit_time: str = ""
    status: str = "OPEN"  # OPEN, CLOSED
    strategy: str = ""'''

new_trade = '''    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: float = 0.0
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    entry_time: str = ""
    exit_time: str = ""
    status: str = "OPEN"  # OPEN, CLOSED
    strategy: str = ""
    stop_loss: float = 0.0
    take_profit: float = 0.0'''

content = content.replace(old_trade, new_trade)

# Fix INSERT statement to include all 14 columns
old_insert = '''        cursor.execute(\'\'\'
            INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        \'\'\', (
            trade.id, trade.symbol, trade.side, trade.entry_price, trade.exit_price,
            trade.quantity, trade.profit_loss, trade.profit_loss_pct,
            trade.entry_time, trade.exit_time, trade.status, trade.strategy
        ))'''

new_insert = '''        cursor.execute(\'\'\'
            INSERT INTO trades (id, symbol, side, entry_price, exit_price, quantity, 
                               profit_loss, profit_loss_pct, entry_time, exit_time, 
                               status, strategy, stop_loss, take_profit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        \'\'\', (
            trade.id, trade.symbol, trade.side, trade.entry_price, trade.exit_price,
            trade.quantity, trade.profit_loss, trade.profit_loss_pct,
            trade.entry_time, trade.exit_time, trade.status, trade.strategy,
            trade.stop_loss, trade.take_profit
        ))'''

content = content.replace(old_insert, new_insert)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("[FIXED] Added stop_loss/take_profit to Trade class")
print("[FIXED] Updated INSERT statement for 14 columns")
