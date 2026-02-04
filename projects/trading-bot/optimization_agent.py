#!/usr/bin/env python3
"""
Continuous Optimization Agent for Trading Bot
Runs every 30 minutes to analyze performance and trigger Codex improvements
"""

import json
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path('paper_trades.db')
REPORT_PATH = Path('optimization_report.json')
BOT_FILE = Path('micro_scalp_bot_v2.py')

class OptimizationAgent:
    """Analyzes trading performance and triggers improvements"""
    
    def __init__(self):
        self.metrics = {}
        self.needs_optimization = False
        self.optimization_reasons = []
    
    def analyze_performance(self):
        """Analyze last 6 hours of trading"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get trades from last 6 hours
        six_hours_ago = (datetime.now() - timedelta(hours=6)).isoformat()
        
        cursor.execute('''
            SELECT profit_loss, profit_loss_pct, status, entry_time
            FROM trades
            WHERE entry_time > ? AND status = 'CLOSED'
        ''', (six_hours_ago,))
        
        trades = cursor.fetchall()
        conn.close()
        
        if not trades:
            logger.info("No closed trades in last 6 hours")
            return
        
        # Calculate metrics
        profits = [t[0] for t in trades if t[0] > 0]
        losses = [t[0] for t in trades if t[0] <= 0]
        
        total_trades = len(trades)
        winning_trades = len(profits)
        losing_trades = len(losses)
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_pnl = sum(t[0] for t in trades)
        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        # Check for consecutive losses
        cursor = sqlite3.connect(DB_PATH).cursor()
        cursor.execute('''
            SELECT profit_loss FROM trades
            WHERE status = 'CLOSED'
            ORDER BY entry_time DESC
            LIMIT 5
        ''')
        recent = cursor.fetchall()
        consecutive_losses = 0
        for t in recent:
            if t[0] <= 0:
                consecutive_losses += 1
            else:
                break
        
        self.metrics = {
            'timestamp': datetime.now().isoformat(),
            'period': '6h',
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'consecutive_losses': consecutive_losses,
            'profit_factor': abs(sum(profits) / sum(losses)) if losses and sum(losses) != 0 else float('inf')
        }
        
        # Check if optimization needed
        self.check_optimization_needed()
        
        # Save report
        self.save_report()
    
    def check_optimization_needed(self):
        """Check if bot needs optimization"""
        m = self.metrics
        
        if m.get('win_rate', 100) < 50:
            self.needs_optimization = True
            self.optimization_reasons.append(f"Win rate {m['win_rate']:.1f}% < 50%")
        
        if m.get('consecutive_losses', 0) >= 3:
            self.needs_optimization = True
            self.optimization_reasons.append(f"{m['consecutive_losses']} consecutive losses")
        
        if m.get('total_pnl', 0) < -50:  # Lost $50 in 6h
            self.needs_optimization = True
            self.optimization_reasons.append(f"P&L ${m['total_pnl']:.2f} < -$50")
    
    def save_report(self):
        """Save optimization report"""
        report = {
            **self.metrics,
            'needs_optimization': self.needs_optimization,
            'optimization_reasons': self.optimization_reasons
        }
        
        with open(REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved. Optimization needed: {self.needs_optimization}")
        if self.optimization_reasons:
            for reason in self.optimization_reasons:
                logger.warning(f"  - {reason}")
    
    def trigger_codex_optimization(self):
        """Trigger Codex to optimize the bot"""
        if not self.needs_optimization:
            logger.info("No optimization needed at this time")
            return
        
        logger.info("🚀 Triggering Codex optimization...")
        
        # Build prompt for Codex
        prompt = self.build_optimization_prompt()
        
        # Run Codex (this will be executed by the cron job)
        logger.info("Optimization prompt ready for Codex")
        logger.info(f"Reasons: {', '.join(self.optimization_reasons)}")
        
        return prompt
    
    def build_optimization_prompt(self) -> str:
        """Build optimization prompt for Codex"""
        m = self.metrics
        
        prompt = f"""Optimize the micro_scalp_bot_v2.py trading bot based on recent performance data.

CURRENT PERFORMANCE (last 6 hours):
- Win rate: {m.get('win_rate', 0):.1f}%
- Total trades: {m.get('total_trades', 0)}
- P&L: ${m.get('total_pnl', 0):.2f}
- Consecutive losses: {m.get('consecutive_losses', 0)}
- Avg profit: ${m.get('avg_profit', 0):.2f}
- Avg loss: ${m.get('avg_loss', 0):.2f}

ISSUES TO FIX:
{chr(10).join('- ' + r for r in self.optimization_reasons)}

OPTIMIZATION TASKS:
1. Analyze SignalGenerator class - improve signal accuracy
2. Review technical indicators (SMA, EMA, volume) - adjust periods if needed
3. Consider adding: RSI, MACD, or Bollinger Bands
4. Improve risk management if losses are too big
5. Add filters to avoid trading in choppy/sideways markets

CONSTRAINTS:
- Keep paper trading mode
- Maintain max 2% risk per trade
- Don't change core architecture
- Test logic thoroughly

When done, save as micro_scalp_bot_v2.py and create a summary of changes."""
        
        return prompt
    
    def run_backtest(self):
        """Run backtest to validate changes"""
        logger.info("Running backtest validation...")
        # This will be implemented with historical data
        pass


def main():
    """Main optimization loop"""
    logger.info("="*60)
    logger.info("🤖 TRADING BOT OPTIMIZATION AGENT")
    logger.info("="*60)
    
    agent = OptimizationAgent()
    
    # Analyze current performance
    logger.info("Analyzing recent performance...")
    agent.analyze_performance()
    
    # Check if optimization needed
    if agent.needs_optimization:
        logger.warning("⚠️ Performance issues detected!")
        prompt = agent.trigger_codex_optimization()
        
        # Save prompt for Codex to use
        with open('codex_optimization_prompt.txt', 'w') as f:
            f.write(prompt)
        
        logger.info("💡 Ready for Codex optimization")
        logger.info("Run: codex exec --full-auto 'Optimize micro_scalp_bot_v2.py based on codex_optimization_prompt.txt'")
    else:
        logger.info("✅ Performance within acceptable limits")
    
    logger.info("="*60)


if __name__ == "__main__":
    main()
