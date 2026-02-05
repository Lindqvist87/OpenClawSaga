#!/usr/bin/env python3
"""
Reset trading database - Remove duplicates
"""

import sqlite3
from pathlib import Path

db_path = Path(r"C:\Users\Hejhej\.openclaw\workspace\projects\trading-bot\paper_trades.db")

if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get current trades
    cursor.execute("SELECT id, symbol, side, entry_price FROM trades")
    trades = cursor.fetchall()
    
    print(f"[INFO] Found {len(trades)} trades")
    
    # Keep only unique trades by ID (keep first occurrence)
    seen_ids = set()
    duplicates = []
    
    for trade in trades:
        if trade[0] in seen_ids:
            duplicates.append(trade[0])
        else:
            seen_ids.add(trade[0])
    
    # Remove duplicates
    for dup_id in duplicates:
        cursor.execute("DELETE FROM trades WHERE id = ?", (dup_id,))
        print(f"[REMOVED] Duplicate trade ID: {dup_id}")
    
    conn.commit()
    conn.close()
    
    print(f"[DONE] Removed {len(duplicates)} duplicates")
else:
    print("[INFO] No database found")
