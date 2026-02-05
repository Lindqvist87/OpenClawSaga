#!/usr/bin/env python3
"""
Apply Codex patch to micro_scalp_bot.py
"""

file_path = r"C:\Users\Hejhej\.openclaw\workspace\projects\trading-bot\micro_scalp_bot.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Replace arrow character (find the line with arrow)
content = content.replace(
    '${trade.entry_price:.2f} → ${current_price:.2f}',
    '${trade.entry_price:.2f} -> ${current_price:.2f}'
)

# Fix 2: Add stop_loss and take_profit to CREATE TABLE
old_schema = "strategy TEXT\n            )"
new_schema = "strategy TEXT,\n                stop_loss REAL,\n                take_profit REAL\n            )"

content = content.replace(old_schema, new_schema)

# Fix 3: Add migration code after CREATE TABLE
old_after_create = "conn.commit()\n        conn.close()\n    \n    def setup_database(self):"
new_after_create = """conn.commit()
        
        # Ensure schema matches INSERT statements for existing databases
        cursor.execute("PRAGMA table_info(trades)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if "stop_loss" not in existing_columns:
            cursor.execute("ALTER TABLE trades ADD COLUMN stop_loss REAL")
        if "take_profit" not in existing_columns:
            cursor.execute("ALTER TABLE trades ADD COLUMN take_profit REAL")
        
        conn.commit()
        conn.close()
    
    def setup_database(self):"""

content = content.replace(old_after_create, new_after_create)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("[FIXED] Applied Codex patch:")
print("  - Replaced arrow character")
print("  - Added stop_loss/take_profit columns")
print("  - Added migration for existing databases")
