#!/usr/bin/env python3
"""Analyze trading performance from paper_trades.db"""
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('paper_trades.db')
cursor = conn.cursor()

# Get all trades
cursor.execute("SELECT * FROM trades ORDER BY entry_time DESC")
trades = cursor.fetchall()

# Get trades from last 6 hours
six_hours_ago = (datetime.now() - timedelta(hours=6)).isoformat()
cursor.execute("SELECT * FROM trades WHERE entry_time > ? ORDER BY entry_time DESC", (six_hours_ago,))
recent_trades = cursor.fetchall()

# Statistics
print("=" * 70)
print("TRADING BOT PERFORMANCE ANALYSIS")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

print(f"\n[OVERALL STATISTICS]")
print(f"  Total trades: {len(trades)}")

closed_trades = [t for t in trades if t[10] == 'CLOSED']
open_trades = [t for t in trades if t[10] == 'OPEN']
winning_trades = [t for t in closed_trades if t[6] and t[6] > 0]
losing_trades = [t for t in closed_trades if t[6] and t[6] <= 0]

print(f"  Closed trades: {len(closed_trades)}")
print(f"  Open trades: {len(open_trades)}")
print(f"  Winning trades: {len(winning_trades)}")
print(f"  Losing trades: {len(losing_trades)}")

if closed_trades:
    win_rate = (len(winning_trades) / len(closed_trades)) * 100
    total_pnl = sum(t[6] for t in closed_trades if t[6])
    avg_profit = sum(t[6] for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(t[6] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    
    print(f"\n[P&L METRICS]")
    print(f"  Win rate: {win_rate:.1f}%")
    print(f"  Total P&L: ${total_pnl:.2f}")
    print(f"  Average profit: ${avg_profit:.2f}")
    print(f"  Average loss: ${avg_loss:.2f}")
else:
    win_rate = 0
    total_pnl = 0
    print(f"\n[!] No closed trades yet - cannot calculate performance metrics")

# Recent trades (last 6h)
print(f"\n[LAST 6 HOURS]")
print(f"  Trades: {len(recent_trades)}")

recent_closed = [t for t in recent_trades if t[10] == 'CLOSED']
if recent_closed:
    recent_pnl = sum(t[6] for t in recent_closed if t[6])
    recent_winners = [t for t in recent_closed if t[6] and t[6] > 0]
    recent_losers = [t for t in recent_closed if t[6] and t[6] <= 0]
    recent_win_rate = (len(recent_winners) / len(recent_closed)) * 100 if recent_closed else 0
    print(f"  Closed: {len(recent_closed)}")
    print(f"  Win rate: {recent_win_rate:.1f}%")
    print(f"  P&L: ${recent_pnl:.2f}")
else:
    print(f"  No closed trades in last 6 hours")

# Check consecutive losses
consecutive_losses = 0
print(f"\n[CONSECUTIVE LOSSES CHECK]")
if closed_trades:
    # Sort by exit time
    sorted_trades = sorted(closed_trades, key=lambda x: x[9] if x[9] else '')
    consecutive_losses = 0
    max_consecutive = 0
    
    for t in sorted_trades:
        pnl = t[6] if t[6] else 0
        if pnl <= 0:
            consecutive_losses += 1
            max_consecutive = max(max_consecutive, consecutive_losses)
        else:
            consecutive_losses = 0
    
    print(f"  Current consecutive losses: {consecutive_losses}")
    print(f"  Max consecutive losses: {max_consecutive}")
else:
    print(f"  N/A - No closed trades")

# Optimization triggers
print(f"\n[OPTIMIZATION TRIGGERS]")
triggers = []
if win_rate < 50 and len(closed_trades) >= 5:
    triggers.append(f"Win rate {win_rate:.1f}% < 50%")
if consecutive_losses >= 3:
    triggers.append(f"{consecutive_losses} consecutive losses")
if total_pnl < -50:
    triggers.append(f"Total P&L ${total_pnl:.2f} < -$50")

if triggers:
    for t in triggers:
        print(f"  [ALERT] {t}")
else:
    print(f"  [OK] No optimization triggers activated")

# Open positions
if open_trades:
    print(f"\n[OPEN POSITIONS]")
    for t in open_trades:
        print(f"  #{t[0]} {t[1]} {t[2]} @ ${t[3]:.2f} (Entry: {t[8]})")

conn.close()

# Save analysis for Codex
with open('performance_analysis.txt', 'w') as f:
    f.write(f"Win Rate: {win_rate:.1f}%\n")
    f.write(f"Total P&L: ${total_pnl:.2f}\n")
    f.write(f"Consecutive Losses: {consecutive_losses}\n")
    f.write(f"Total Closed Trades: {len(closed_trades)}\n")
    f.write(f"Optimization Needed: {'YES' if triggers else 'NO'}\n")
    if triggers:
        f.write(f"Triggers: {', '.join(triggers)}\n")
