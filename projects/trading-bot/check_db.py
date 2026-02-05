import sqlite3
conn=sqlite3.connect('paper_trades.db')
c=conn.cursor()
c.execute("SELECT COUNT(*),SUM(CASE WHEN status='OPEN' THEN 1 ELSE 0 END) FROM trades")
r=c.fetchone()
print(f'Total: {r[0] or 0}, Open: {r[1] or 0}')
c.execute("SELECT id, symbol, side, entry_price, quantity, status FROM trades LIMIT 5")
print("\nTrades:")
for row in c.fetchall():
    print(f"  {row}")
conn.close()