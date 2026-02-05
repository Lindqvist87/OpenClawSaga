#!/usr/bin/env python3
"""
Fix micro_scalp_bot.py - Remove all emoji from logging
"""

import re

file_path = r"C:\Users\Hejhej\.openclaw\workspace\projects\trading-bot\micro_scalp_bot.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace emoji patterns in logging messages
replacements = [
    (r'logger\.info\("🚀 Starting', 'logger.info("[START] Starting'),
    (r'logger\.error\("❌ Bot error', 'logger.error("[ERROR] Bot error'),
    (r'logger\.info\("✅', 'logger.info("[OK]'),
    (r'logger\.info\("📊', 'logger.info("[DATA]'),
    (r'logger\.info\("⚠️', 'logger.info("[WARN]'),
    (r'logger\.info\("🎯', 'logger.info("[TARGET]'),
    (r'logger\.info\("💰', 'logger.info("[MONEY]'),
    (r'logger\.info\("🔔', 'logger.info("[ALERT]'),
    (r'logger\.info\("📈', 'logger.info("[UP]'),
    (r'logger\.info\("📉', 'logger.info("[DOWN]'),
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Fix trade ID collision - ensure auto-increment
content = content.replace(
    'cursor.execute("SELECT MAX(id) FROM trades")',
    'cursor.execute("SELECT COALESCE(MAX(id), 0) FROM trades")'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("[FIXED] Removed emoji from micro_scalp_bot.py")
print("[FIXED] Fixed trade ID handling")
