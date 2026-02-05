#!/usr/bin/env python3
"""
Find and remove all remaining emoji from micro_scalp_bot.py
"""

import re

file_path = r"C:\Users\Hejhej\.openclaw\workspace\projects\trading-bot\micro_scalp_bot.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all emoji
emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')

matches = emoji_pattern.findall(content)
if matches:
    print(f"[FOUND] {len(matches)} emoji: {matches}")
else:
    print("[OK] No emoji found")

# Remove all emoji
content_clean = emoji_pattern.sub('', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content_clean)

print("[DONE] All emoji removed")
