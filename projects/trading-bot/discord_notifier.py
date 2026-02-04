"""
Discord Notifications for Trading Bot
Sends alerts and reports to Discord channel via webhook
"""

import requests
import json
from datetime import datetime
from typing import Dict, Optional

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1468661709098192949/zcK1T8XJTi1mV77gyBldtn2pA8BhtZUm1q8ePVkzHY3y_rpEIJ_ldvZmBSqvFB6UIyLe"

class DiscordNotifier:
    """Sends trading notifications to Discord"""
    
    def __init__(self):
        self.webhook_url = DISCORD_WEBHOOK_URL
        self.enabled = True
    
    def send_message(self, content: str, embeds: list = None) -> bool:
        """Send message to Discord"""
        try:
            payload = {"content": content}
            if embeds:
                payload["embeds"] = embeds
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            return response.status_code == 204
            
        except Exception as e:
            print(f"Discord notification failed: {e}")
            return False
    
    def notify_trade_opened(self, symbol: str, side: str, price: float, quantity: float, confidence: float):
        """Notify when trade is opened"""
        embed = {
            "title": f"📊 Trade Opened: {symbol}",
            "description": f"{side} position opened at ${price:.2f}",
            "color": 3066993 if side == "BUY" else 15158332,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {"name": "Side", "value": side, "inline": True},
                {"name": "Price", "value": f"${price:.2f}", "inline": True},
                {"name": "Quantity", "value": f"{quantity:.6f}", "inline": True},
                {"name": "Confidence", "value": f"{confidence:.0%}", "inline": True}
            ],
            "footer": {"text": "Micro-Scalp Trading Bot"}
        }
        
        self.send_message(f"🦞 New trade opened for {symbol}", [embed])
    
    def notify_trade_closed(self, symbol: str, side: str, entry: float, exit: float, pnl: float, pnl_pct: float):
        """Notify when trade is closed"""
        is_profit = pnl > 0
        emoji = "🟢" if is_profit else "🔴"
        color = 3066993 if is_profit else 15158332
        
        embed = {
            "title": f"{emoji} Trade Closed: {symbol}",
            "description": f"{side} position closed",
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {"name": "Entry", "value": f"${entry:.2f}", "inline": True},
                {"name": "Exit", "value": f"${exit:.2f}", "inline": True},
                {"name": "P&L", "value": f"${pnl:+.2f}", "inline": True},
                {"name": "P&L %", "value": f"{pnl_pct:+.2f}%", "inline": True}
            ],
            "footer": {"text": "Micro-Scalp Trading Bot"}
        }
        
        self.send_message(f"{emoji} Trade closed for {symbol}", [embed])
    
    def notify_stop_loss(self, symbol: str, price: float, loss: float):
        """Notify stop loss triggered"""
        embed = {
            "title": f"🛑 Stop Loss Triggered: {symbol}",
            "description": f"Position stopped at ${price:.2f}",
            "color": 15158332,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {"name": "Stop Price", "value": f"${price:.2f}", "inline": True},
                {"name": "Loss", "value": f"${loss:.2f}", "inline": True}
            ],
            "footer": {"text": "Risk Management"}
        }
        
        self.send_message(f"🛑 Stop loss triggered for {symbol}", [embed])
    
    def notify_take_profit(self, symbol: str, price: float, profit: float):
        """Notify take profit triggered"""
        embed = {
            "title": f"✅ Take Profit: {symbol}",
            "description": f"Target reached at ${price:.2f}",
            "color": 3066993,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {"name": "Exit Price", "value": f"${price:.2f}", "inline": True},
                {"name": "Profit", "value": f"${profit:.2f}", "inline": True}
            ],
            "footer": {"text": "Profit Target Reached"}
        }
        
        self.send_message(f"✅ Take profit hit for {symbol}!", [embed])
    
    def notify_daily_summary(self, stats: Dict):
        """Send daily trading summary"""
        total_trades = stats.get('total_trades', 0)
        win_rate = stats.get('win_rate', 0)
        total_pnl = stats.get('total_pnl', 0)
        balance = stats.get('balance', 1000)
        
        is_profit = total_pnl >= 0
        color = 3066993 if is_profit else 15158332
        emoji = "📈" if is_profit else "📉"
        
        embed = {
            "title": f"{emoji} Daily Trading Summary",
            "description": f"Performance for {datetime.now().strftime('%Y-%m-%d')}",
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {"name": "Total Trades", "value": str(total_trades), "inline": True},
                {"name": "Win Rate", "value": f"{win_rate:.1f}%", "inline": True},
                {"name": "Total P&L", "value": f"${total_pnl:+.2f}", "inline": True},
                {"name": "Balance", "value": f"${balance:.2f}", "inline": True}
            ],
            "footer": {"text": "Micro-Scalp Trading Bot - Daily Report"}
        }
        
        self.send_message(f"{emoji} Daily summary ready!", [embed])
    
    def notify_error(self, error_message: str):
        """Notify on errors"""
        embed = {
            "title": "⚠️ Trading Bot Error",
            "description": error_message[:1000],
            "color": 15158332,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Check logs for details"}
        }
        
        self.send_message("⚠️ Trading bot encountered an error", [embed])
    
    def notify_system_status(self, is_operational: bool, message: str = ""):
        """Notify system status"""
        color = 3066993 if is_operational else 15158332
        emoji = "🟢" if is_operational else "🔴"
        status = "Operational" if is_operational else "Issue Detected"
        
        embed = {
            "title": f"{emoji} Bot Status: {status}",
            "description": message or "Trading bot status update",
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.send_message(f"{emoji} Trading bot status update", [embed])

# Global instance
discord = DiscordNotifier()

if __name__ == "__main__":
    # Test notifications
    print("Testing Discord notifications...")
    
    discord.notify_system_status(True, "Bot started successfully")
    discord.notify_trade_opened("BTCUSDT", "BUY", 72500.50, 0.0015, 0.75)
    discord.notify_daily_summary({
        'total_trades': 5,
        'win_rate': 60.0,
        'total_pnl': 25.50,
        'balance': 1025.50
    })
    
    print("Test notifications sent!")
