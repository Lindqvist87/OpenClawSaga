# Windows PowerShell Script for Trading Bot
# Run this to collect data without bash dependencies

# Change to trading bot directory
Set-Location -Path "C:\Users\Hejhej\.openclaw\workspace\projects\trading-bot"

# Run Python data collection
python ..\..\.openclaw\scripts\data_collection.py

# Check if successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Data collection successful" -ForegroundColor Green
} else {
    Write-Host "❌ Data collection failed" -ForegroundColor Red
}

# Optional: Send Discord notification
# (requires discord_config.py to be set up)
