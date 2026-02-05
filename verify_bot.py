#!/usr/bin/env python3
"""
Final verification of micro_scalp_bot.py
"""

file_path = r"C:\Users\Hejhej\.openclaw\workspace\projects\trading-bot\micro_scalp_bot.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check 1: Find all emoji
import re
emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251\u274c\u2705\u26a0]+')
matches = emoji_pattern.findall(content)

print("=== VERIFICATION REPORT ===")
print(f"\n1. EMOJI CHECK:")
if matches:
    print(f"   ❌ FOUND {len(matches)} emoji: {matches}")
else:
    print(f"   ✅ No emoji found")

# Check 2: Trade class fields
print(f"\n2. TRADE CLASS FIELDS:")
trade_fields = ['stop_loss', 'take_profit']
for field in trade_fields:
    if field in content:
        print(f"   ✅ Has '{field}'")
    else:
        print(f"   ❌ Missing '{field}'")

# Check 3: INSERT statement
print(f"\n3. INSERT STATEMENT:")
if 'stop_loss, take_profit' in content and 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)' in content:
    print(f"   ✅ INSERT has 14 columns and 14 values")
else:
    print(f"   ❌ INSERT mismatch")

# Check 4: Count ? in INSERT
import re
insert_match = re.search(r'INSERT INTO trades.*?VALUES \((\?[,\s]*)+\)', content, re.DOTALL)
if insert_match:
    q_count = insert_match.group(0).count('?')
    print(f"   Values count: {q_count}")

print(f"\n=== END REPORT ===")
