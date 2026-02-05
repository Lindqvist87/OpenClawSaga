#!/usr/bin/env python3
"""
Fix database schema - Add AUTOINCREMENT to ID
"""

import sqlite3
from pathlib import Path
import shutil

db_path = Path(r"C:\Users\Hejhej\.openclaw\workspace\projects\trading-bot\paper_trades.db")

# Backup old database
if db_path.exists():
    backup_path = db_path.with_suffix('.db.backup')
    shutil.copy(db_path, backup_path)
    print("[BACKUP] Created backup")

# Create new database with correct schema
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Drop and recreate trades table with AUTOINCREMENT
cursor.execute("DROP TABLE IF EXISTS trades")
cursor.execute('''
    CREATE TABLE trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        side TEXT,
        entry_price REAL,
        exit_price REAL,
        quantity REAL,
        profit_loss REAL,
        profit_loss_pct REAL,
        entry_time TEXT,
        exit_time TEXT,
        status TEXT DEFAULT 'OPEN',
        strategy TEXT,
        stop_loss REAL,
        take_profit REAL
    )
''')

conn.commit()
conn.close()

print("[FIXED] Database recreated with AUTOINCREMENT")
