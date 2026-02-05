# Codex Optimization Task - Trading Bot Bug Fix

## Problem Description
The trading bot has a critical bug where it generates SELL signals but does NOT close the corresponding BUY trades that are open.

## Current State
- 3 BUY trades opened 2026-02-04 21:35
- Bot generates SELL signals every minute since 06:50 today
- NO trades are being closed
- Open positions: BTCUSDT, ETHUSDT, SOLUSDT

## Log Evidence
```
2026-02-05 06:50:57 - SELL signal for BTCUSDT: Downtrend confirmed
2026-02-05 06:50:57 - SELL signal for ETHUSDT: Downtrend confirmed
2026-02-05 06:50:57 - SELL signal for SOLUSDT: Downtrend confirmed
... (repeats every minute)
```

## Files to Analyze
1. micro_scalp_bot_v2.py - Main bot logic
2. Look at: SignalGenerator.generate_signal() method
3. Look at: How signals connect to trade closing logic
4. Look at: The main trading loop

## Required Fixes
1. Fix the signal-to-trade-closing logic so SELL signals properly close open BUY positions
2. Ensure stop-loss and take-profit are being checked regularly
3. Add proper error handling for trade closing operations
4. Make sure the bot doesn't open new positions in the same direction when one is already open

## Testing Requirements
After fixing, the bot should:
- Close BUY trades when SELL signal is generated (or use stop-loss/take-profit)
- Properly manage open positions
- Log all trade closures with exit reasons

## Constraints
- Paper trading mode only (no live trading)
- Keep all existing risk management logic
- Maintain the scalping strategy parameters
