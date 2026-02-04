#!/usr/bin/env python3
"""
Micro-Scalp Trading Bot - Paper Trading Mode
Conservative strategy: Small, frequent profits with strict risk management
"""

import json
import time
import logging
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade"""
    id: int = 0
    symbol: str = ""
    side: str = ""  # BUY or SELL
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: float = 0.0
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    entry_time: str = ""
    exit_time: str = ""
    status: str = "OPEN"  # OPEN, CLOSED
    strategy: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PriceMonitor:
    """Monitors cryptocurrency prices via Binance API"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.price_cache = {}
        self.last_update = None
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol (e.g., 'BTCUSDT')"""
        try:
            endpoint = f"{self.base_url}/api/v3/ticker/price"
            response = requests.get(endpoint, params={"symbol": symbol}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                self.price_cache[symbol] = {
                    'price': price,
                    'timestamp': datetime.now()
                }
                return price
            else:
                logger.error(f"Error fetching price for {symbol}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Exception fetching price for {symbol}: {e}")
            return None
    
    def get_klines(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[Dict]:
        """Get candlestick data for technical analysis"""
        try:
            endpoint = f"{self.base_url}/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                candles = []
                for item in data:
                    candles.append({
                        'timestamp': item[0],
                        'open': float(item[1]),
                        'high': float(item[2]),
                        'low': float(item[3]),
                        'close': float(item[4]),
                        'volume': float(item[5])
                    })
                return candles
            else:
                logger.error(f"Error fetching klines for {symbol}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Exception fetching klines for {symbol}: {e}")
            return []


class SignalGenerator:
    """Generates trading signals based on technical indicators"""
    
    def __init__(self):
        self.signals = []
    
    def calculate_sma(self, prices: List[float], period: int) -> float:
        """Simple Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        return sum(prices[-period:]) / period
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Exponential Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def detect_volume_spike(self, volumes: List[float], threshold: float = 2.0) -> bool:
        """Detect if current volume is spiking"""
        if len(volumes) < 20:
            return False
        
        avg_volume = sum(volumes[-20:-1]) / 19
        current_volume = volumes[-1]
        
        return current_volume > (avg_volume * threshold)
    
    def generate_signal(self, candles: List[Dict]) -> Dict:
        """Generate trading signal from candle data"""
        if len(candles) < 50:
            return {'signal': 'HOLD', 'reason': 'Insufficient data'}
        
        closes = [c['close'] for c in candles]
        volumes = [c['volume'] for c in candles]
        
        # Calculate moving averages
        sma_10 = self.calculate_sma(closes, 10)
        sma_20 = self.calculate_sma(closes, 20)
        sma_50 = self.calculate_sma(closes, 50)
        ema_12 = self.calculate_ema(closes, 12)
        ema_26 = self.calculate_ema(closes, 26)
        
        current_price = closes[-1]
        
        # Volume spike detection
        volume_spike = self.detect_volume_spike(volumes)
        
        # Generate signals
        signal = 'HOLD'
        reason = 'No clear signal'
        confidence = 0.0
        
        # Bullish signals
        if sma_10 > sma_20 and sma_20 > sma_50:
            if ema_12 > ema_26:
                if volume_spike:
                    signal = 'BUY'
                    reason = 'Strong uptrend with volume spike'
                    confidence = 0.8
                else:
                    signal = 'BUY'
                    reason = 'Uptrend confirmed'
                    confidence = 0.6
        
        # Bearish signals
        elif sma_10 < sma_20 and sma_20 < sma_50:
            if ema_12 < ema_26:
                signal = 'SELL'
                reason = 'Downtrend confirmed'
                confidence = 0.6
        
        return {
            'signal': signal,
            'reason': reason,
            'confidence': confidence,
            'current_price': current_price,
            'sma_10': sma_10,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'volume_spike': volume_spike
        }


class RiskManager:
    """Manages trading risk and position sizing"""
    
    def __init__(self, max_daily_loss_pct: float = 5.0, max_position_pct: float = 2.0):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_position_pct = max_position_pct
        self.daily_loss = 0.0
        self.daily_loss_pct = 0.0
        self.trades_today = 0
        self.max_trades_per_day = 10
        self.last_reset = datetime.now().date()
    
    def check_daily_reset(self):
        """Reset daily counters"""
        today = datetime.now().date()
        if today != self.last_reset:
            self.daily_loss = 0.0
            self.daily_loss_pct = 0.0
            self.trades_today = 0
            self.last_reset = today
            logger.info("Daily counters reset")
    
    def can_trade(self, portfolio_value: float) -> Tuple[bool, str]:
        """Check if trading is allowed"""
        self.check_daily_reset()
        
        # Check daily loss limit
        if self.daily_loss_pct >= self.max_daily_loss_pct:
            return False, f"Daily loss limit reached: {self.daily_loss_pct:.2f}%"
        
        # Check max trades per day
        if self.trades_today >= self.max_trades_per_day:
            return False, f"Max trades per day reached: {self.max_trades_per_day}"
        
        return True, "Trading allowed"
    
    def calculate_position_size(self, portfolio_value: float, entry_price: float) -> float:
        """Calculate position size based on risk limits"""
        position_value = portfolio_value * (self.max_position_pct / 100)
        quantity = position_value / entry_price
        return round(quantity, 6)
    
    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """Calculate stop loss price (1% loss max)"""
        stop_pct = 0.01  # 1% stop loss
        
        if side == 'BUY':
            return entry_price * (1 - stop_pct)
        else:
            return entry_price * (1 + stop_pct)
    
    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """Calculate take profit price (2% gain target)"""
        profit_pct = 0.02  # 2% take profit
        
        if side == 'BUY':
            return entry_price * (1 + profit_pct)
        else:
            return entry_price * (1 - profit_pct)
    
    def update_daily_loss(self, trade_pnl: float, portfolio_value: float):
        """Update daily loss tracking"""
        if trade_pnl < 0:
            self.daily_loss += abs(trade_pnl)
            self.daily_loss_pct = (self.daily_loss / portfolio_value) * 100
        
        self.trades_today += 1


class PaperTrader:
    """Paper trading simulation - no real money"""
    
    def __init__(self, initial_balance: float = 1000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.portfolio_value = initial_balance
        self.open_trades: List[Trade] = []
        self.trade_history: List[Trade] = []
        self.trade_id_counter = 0
        
        # Setup database
        self.db_path = Path('paper_trades.db')
        self.setup_database()
    
    def setup_database(self):
        """Setup SQLite database for trade tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                side TEXT,
                entry_price REAL,
                exit_price REAL,
                quantity REAL,
                profit_loss REAL,
                profit_loss_pct REAL,
                entry_time TEXT,
                exit_time TEXT,
                status TEXT,
                strategy TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def open_trade(self, symbol: str, side: str, price: float, quantity: float, strategy: str = "micro_scalp") -> Optional[Trade]:
        """Open a new paper trade"""
        trade_cost = price * quantity
        
        if trade_cost > self.balance * 0.95:  # Keep 5% buffer
            logger.warning(f"Insufficient balance for trade. Required: ${trade_cost:.2f}, Available: ${self.balance:.2f}")
            return None
        
        self.trade_id_counter += 1
        
        trade = Trade(
            id=self.trade_id_counter,
            symbol=symbol,
            side=side,
            entry_price=price,
            quantity=quantity,
            entry_time=datetime.now().isoformat(),
            status="OPEN",
            strategy=strategy
        )
        
        self.open_trades.append(trade)
        self.balance -= trade_cost
        
        logger.info(f"OPENED {side} trade: {symbol} @ ${price:.2f} x {quantity}")
        
        # Save to database
        self.save_trade(trade)
        
        return trade
    
    def close_trade(self, trade_id: int, exit_price: float) -> Optional[Trade]:
        """Close an open trade"""
        trade = None
        for t in self.open_trades:
            if t.id == trade_id:
                trade = t
                break
        
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return None
        
        trade.exit_price = exit_price
        trade.exit_time = datetime.now().isoformat()
        trade.status = "CLOSED"
        
        # Calculate P&L
        if trade.side == 'BUY':
            trade.profit_loss = (exit_price - trade.entry_price) * trade.quantity
        else:
            trade.profit_loss = (trade.entry_price - exit_price) * trade.quantity
        
        trade.profit_loss_pct = (trade.profit_loss / (trade.entry_price * trade.quantity)) * 100
        
        # Update balance
        self.balance += (exit_price * trade.quantity)
        
        # Move to history
        self.open_trades.remove(trade)
        self.trade_history.append(trade)
        
        logger.info(f"CLOSED trade {trade_id}: P&L = ${trade.profit_loss:.2f} ({trade.profit_loss_pct:.2f}%)")
        
        # Update database
        self.update_trade(trade)
        
        return trade
    
    def save_trade(self, trade: Trade):
        """Save trade to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.id, trade.symbol, trade.side, trade.entry_price, trade.exit_price,
            trade.quantity, trade.profit_loss, trade.profit_loss_pct,
            trade.entry_time, trade.exit_time, trade.status, trade.strategy
        ))
        
        conn.commit()
        conn.close()
    
    def update_trade(self, trade: Trade):
        """Update trade in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE trades SET exit_price=?, exit_time=?, status=?, profit_loss=?, profit_loss_pct=?
            WHERE id=?
        ''', (trade.exit_price, trade.exit_time, trade.status, trade.profit_loss, trade.profit_loss_pct, trade.id))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """Get trading statistics"""
        closed_trades = [t for t in self.trade_history if t.status == 'CLOSED']
        
        if not closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'balance': self.balance,
                'open_trades': len(self.open_trades)
            }
        
        winning = sum(1 for t in closed_trades if t.profit_loss > 0)
        losing = sum(1 for t in closed_trades if t.profit_loss <= 0)
        total_pnl = sum(t.profit_loss for t in closed_trades)
        
        return {
            'total_trades': len(closed_trades),
            'winning_trades': winning,
            'losing_trades': losing,
            'win_rate': (winning / len(closed_trades)) * 100,
            'total_pnl': total_pnl,
            'balance': self.balance,
            'open_trades': len(self.open_trades)
        }


class MicroScalpBot:
    """Main trading bot - Micro-Scalp strategy"""
    
    def __init__(self, symbols: List[str] = None):
        self.symbols = symbols or ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        self.price_monitor = PriceMonitor()
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager()
        self.trader = PaperTrader(initial_balance=1000.0)
        
        self.running = False
        self.check_interval = 60  # Check every 60 seconds
    
    def check_open_trades(self):
        """Check if any open trades should be closed"""
        current_prices = {}
        
        for trade in self.trader.open_trades[:]:
            # Get current price
            if trade.symbol not in current_prices:
                price = self.price_monitor.get_price(trade.symbol)
                if price:
                    current_prices[trade.symbol] = price
            
            current_price = current_prices.get(trade.symbol)
            if not current_price:
                continue
            
            # Check stop loss and take profit
            stop_loss = self.risk_manager.calculate_stop_loss(trade.entry_price, trade.side)
            take_profit = self.risk_manager.calculate_take_profit(trade.entry_price, trade.side)
            
            if trade.side == 'BUY':
                if current_price <= stop_loss:
                    logger.info(f"STOP LOSS triggered for {trade.symbol}")
                    self.trader.close_trade(trade.id, current_price)
                    self.risk_manager.update_daily_loss(
                        (current_price - trade.entry_price) * trade.quantity,
                        self.trader.balance
                    )
                elif current_price >= take_profit:
                    logger.info(f"TAKE PROFIT triggered for {trade.symbol}")
                    self.trader.close_trade(trade.id, current_price)
                    self.risk_manager.update_daily_loss(
                        (current_price - trade.entry_price) * trade.quantity,
                        self.trader.balance
                    )
            
            else:  # SELL
                if current_price >= stop_loss:
                    logger.info(f"STOP LOSS triggered for {trade.symbol}")
                    self.trader.close_trade(trade.id, current_price)
                    self.risk_manager.update_daily_loss(
                        (trade.entry_price - current_price) * trade.quantity,
                        self.trader.balance
                    )
                elif current_price <= take_profit:
                    logger.info(f"TAKE PROFIT triggered for {trade.symbol}")
                    self.trader.close_trade(trade.id, current_price)
                    self.risk_manager.update_daily_loss(
                        (trade.entry_price - current_price) * trade.quantity,
                        self.trader.balance
                    )
    
    def check_new_signals(self):
        """Check for new trading signals"""
        # Check if we can trade
        can_trade, reason = self.risk_manager.can_trade(self.trader.balance)
        if not can_trade:
            logger.warning(f"Trading blocked: {reason}")
            return
        
        for symbol in self.symbols:
            # Skip if already have open trade for this symbol
            if any(t.symbol == symbol for t in self.trader.open_trades):
                continue
            
            # Get price data
            candles = self.price_monitor.get_klines(symbol, interval='5m', limit=50)
            if not candles:
                continue
            
            # Generate signal
            signal = self.signal_generator.generate_signal(candles)
            
            if signal['signal'] == 'BUY' and signal['confidence'] >= 0.6:
                logger.info(f"BUY signal for {symbol}: {signal['reason']} (confidence: {signal['confidence']})")
                
                # Calculate position size
                current_price = signal['current_price']
                quantity = self.risk_manager.calculate_position_size(
                    self.trader.balance + sum(t.entry_price * t.quantity for t in self.trader.open_trades),
                    current_price
                )
                
                # Open trade
                self.trader.open_trade(symbol, 'BUY', current_price, quantity)
            
            elif signal['signal'] == 'SELL' and signal['confidence'] >= 0.6:
                logger.info(f"SELL signal for {symbol}: {signal['reason']} (confidence: {signal['confidence']})")
                
                # For paper trading, we'll skip short selling for now
                # Only trade BUY signals in paper mode
                pass
    
    def print_status(self):
        """Print current bot status"""
        stats = self.trader.get_stats()
        
        print("\n" + "="*60)
        print(f"🤖 MICRO-SCALP BOT STATUS")
        print("="*60)
        print(f"Balance: ${stats['balance']:.2f}")
        print(f"Open Trades: {stats['open_trades']}")
        print(f"Total Closed Trades: {stats['total_trades']}")
        print(f"Win Rate: {stats['win_rate']:.1f}%")
        print(f"Total P&L: ${stats['total_pnl']:.2f}")
        print(f"Daily Loss: {self.risk_manager.daily_loss_pct:.2f}%")
        print("="*60)
        
        if self.trader.open_trades:
            print("\n📊 OPEN TRADES:")
            for trade in self.trader.open_trades:
                current_price = self.price_monitor.get_price(trade.symbol)
                if current_price:
                    pnl = (current_price - trade.entry_price) * trade.quantity
                    pnl_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
                    print(f"  {trade.symbol}: ${trade.entry_price:.2f} → ${current_price:.2f} | P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        
        print("")
    
    def run(self):
        """Main bot loop"""
        logger.info("🚀 Starting Micro-Scalp Bot (PAPER TRADING MODE)")
        logger.info(f"Symbols: {self.symbols}")
        logger.info(f"Initial Balance: ${self.trader.initial_balance:.2f}")
        
        self.running = True
        
        try:
            while self.running:
                # Check existing trades
                self.check_open_trades()
                
                # Check for new signals
                self.check_new_signals()
                
                # Print status
                self.print_status()
                
                # Wait before next check
                logger.info(f"Waiting {self.check_interval}s before next check...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            self.running = False


def main():
    """Entry point"""
    print("🦞 MICRO-SCALP TRADING BOT")
    print("="*60)
    print("⚠️  PAPER TRADING MODE - NO REAL MONEY ⚠️")
    print("="*60)
    print()
    
    # Create bot
    bot = MicroScalpBot(
        symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    )
    
    # Run
    bot.run()


if __name__ == "__main__":
    main()
