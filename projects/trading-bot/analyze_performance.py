#!/usr/bin/env python3
"""Analyze trading performance for last 6 hours"""
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('paper_trades.db')
cursor = conn.cursor()

# Get trades from last 6 hours
six_hours_ago = (datetime.now() - timedelta(hours=6)).isoformat()

cursor.execute('''
    SELECT 
        COUNT(*) as total_trades,
        SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN profit_loss <= 0 THEN 1 ELSE 0 END) as losses,
        SUM(profit_loss) as total_pnl,
        AVG(profit_loss_pct) as avg_pnl_pct
    FROM trades 
    WHERE status = 'CLOSED' AND exit_time >= ?
''', (six_hours_ago,))

result = cursor.fetchone()
total_trades = result[0] or 0
wins = result[1] or 0
losses = result[2] or 0
total_pnl = result[3] or 0
avg_pnl_pct = result[4] or 0

win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

print(f"=== 6-HOUR PERFORMANCE ANALYSIS ===")
print(f"Total Trades (6h): {total_trades}")
print(f"Wins: {wins}")
print(f"Losses: {losses}")
print(f"Win Rate: {win_rate:.1f}%")
print(f"Total P&L: ${total_pnl:.2f}")
print(f"Avg P&L %: {avg_pnl_pct:.2f}%")

# Check for consecutive losses
cursor.execute('''
    SELECT profit_loss > 0 as is_win
    FROM trades 
    WHERE status = 'CLOSED' 
    ORDER BY exit_time DESC
    LIMIT 10
''')
recent = cursor.fetchall()
consecutive_losses = 0
for row in recent:
    if row[0] == 0:  # Loss
        consecutive_losses += 1
    else:
        break
print(f"Consecutive Losses: {consecutive_losses}")

# Determine if optimization needed
print("\n=== OPTIMIZATION CHECK ===")
needs_optimization = False
reasons = []

if total_trades >= 3 and win_rate < 50:
    needs_optimization = True
    reasons.append(f"Win rate {win_rate:.1f}% < 50%")

if consecutive_losses >= 3:
    needs_optimization = True
    reasons.append(f"{consecutive_losses} consecutive losses")

if total_pnl < -50:
    needs_optimization = True
    reasons.append(f"P&L ${total_pnl:.2f} < -$50")

if needs_optimization:
    print("STATUS: OPTIMIZATION REQUIRED")
    for r in reasons:
        print(f"  - {r}")
else:
    print("STATUS: NO OPTIMIZATION NEEDED")
    print("  - All metrics within acceptable thresholds")

conn.close()
