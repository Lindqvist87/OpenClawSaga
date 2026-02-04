#!/bin/bash
# Quick Start Script for Micro-Scalp Trading Bot

echo "🦞 MICRO-SCALP TRADING BOT - QUICK START"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found"

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

echo "✅ pip found"

# Install required packages
echo ""
echo "📦 Installing required packages..."
pip install requests sqlite3

# Create config from template
echo ""
echo "⚙️  Setting up configuration..."
if [ ! -f "config.py" ]; then
    cp config_template.py config.py
    echo "✅ Created config.py from template"
else
    echo "✅ config.py already exists"
fi

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p reports
mkdir -p logs

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo ""
echo "To start paper trading:"
echo "  python3 micro_scalp_bot.py"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - This is PAPER TRADING (fake money)"
echo "   - Let it run for 1-2 weeks to validate strategy"
echo "   - Only then consider switching to live trading"
echo "   - NEVER risk more than you can afford to lose"
echo "=========================================="
