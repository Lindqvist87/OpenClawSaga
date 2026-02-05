#!/usr/bin/env python3
"""
Remove ALL emoji from micro_scalp_bot.py
"""

import re

file_path = r"C:\Users\Hejhej\.openclaw\workspace\projects\trading-bot\micro_scalp_bot.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and list all emoji patterns in logger calls
emoji_patterns = [
    r'logger\.\w+\(["\'][^"\']*([🚀❌✅📊⚠️🎯💰🔔📈📉🤖🦞])[^"\']*["\']\)',
]

# Replace all emoji with text equivalents
replacements = {
    '🚀': '[START]',
    '❌': '[ERROR]',
    '✅': '[OK]',
    '📊': '[DATA]',
    '⚠️': '[WARN]',
    '🎯': '[TARGET]',
    '💰': '[MONEY]',
    '🔔': '[ALERT]',
    '📈': '[UP]',
    '📉': '[DOWN]',
    '🤖': '[BOT]',
    '🦞': '[BOT]',
}

for emoji, replacement in replacements.items():
    content = content.replace(emoji, replacement)

# Also remove from print statements
for emoji, replacement in replacements.items():
    content = content.replace(emoji, replacement)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("[FIXED] Removed all emoji from micro_scalp_bot.py")
