import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('paper_trades.db')
cursor = conn.cursor()

# Get last 6 hours timestamp
six_hours_ago = (datetime.now() - timedelta(hours=6)).isoformat()

# Query all trades in last 6h
cursor.execute('''
    SELECT * FROM trades 
    WHERE entry_time >= ? 
    ORDER BY entry_time DESC
''', (six_hours_ago,))

trades = cursor.fetchall()
print('=== TRADES IN LAST 6 HOURS ===')
print(f'Total trades: {len(trades)}')

closed_trades = [t for t in trades if t[10] == 'CLOSED']
open_trades = [t for t in trades if t[10] == 'OPEN']

print(f'Closed trades: {len(closed_trades)}')
print(f'Open trades: {len(open_trades)}')

if closed_trades:
    wins = [t for t in closed_trades if t[6] > 0]
    losses = [t for t in closed_trades if t[6] <= 0]
    total_pnl = sum(t[6] for t in closed_trades)
    win_rate = len(wins) / len(closed_trades) * 100
    
    print(f'\nWinning trades: {len(wins)}')
    print(f'Losing trades: {len(losses)}')
    print(f'Win rate: {win_rate:.1f}%')
    print(f'Total P&L: ${total_pnl:.2f}')
    
    # Check for consecutive losses
    cursor.execute('''
        SELECT profit_loss FROM trades 
        WHERE status = 'CLOSED' AND entry_time >= ?
        ORDER BY exit_time DESC
    ''', (six_hours_ago,))
    
    pnl_list = [r[0] for r in cursor.fetchall()]
    consecutive_losses = 0
    for pnl in pnl_list:
        if pnl <= 0:
            consecutive_losses += 1
        else:
            break
    print(f'Consecutive losses: {consecutive_losses}')
else:
    print('\nNo closed trades to analyze')

# Show open trades
if open_trades:
    print('\n=== OPEN TRADES ===')
    for t in open_trades:
        print(f"ID {t[0]}: {t[1]} {t[2]} @ ${t[3]:.2f} - Opened: {t[8]}")

conn.close()
