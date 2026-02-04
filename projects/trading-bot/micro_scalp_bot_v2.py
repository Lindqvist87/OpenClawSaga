#!/usr/bin/env python3
"""
Micro-Scalp Trading Bot v2.0 - Enhanced Paper Trading
======================================================
Features:
- Technical indicators: RSI, MACD, Bollinger Bands, SMA, EMA
- Improved signal generation with multi-indicator confirmation
- Backtesting capability with historical data
- Enhanced risk management with dynamic position sizing
- Comprehensive logging and reporting
- Web dashboard for real-time monitoring
"""

import json
import time
import logging
import sqlite3
import asyncio
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from collections import deque
import requests
import numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser

# Setup logging with rotating file handler
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('trading_bot.log', maxBytes=5*1024*1024, backupCount=3),
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
    stop_loss: float = 0.0
    take_profit: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Signal:
    """Represents a trading signal"""
    symbol: str = ""
    signal: str = "HOLD"  # BUY, SELL, HOLD
    confidence: float = 0.0
    reason: str = ""
    indicators: Dict = None
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        return data


class TechnicalIndicators:
    """Comprehensive technical analysis indicators"""
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> Optional[float]:
        """Simple Moving Average"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> Optional[float]:
        """Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Optional[float]]:
        """Moving Average Convergence Divergence"""
        if len(prices) < slow + signal:
            return {'macd': None, 'signal': None, 'histogram': None}
        
        # Calculate EMAs
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow)
        
        if ema_fast is None or ema_slow is None:
            return {'macd': None, 'signal': None, 'histogram': None}
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD)
        # We need historical MACD values, approximate using current approach
        macd_values = []
        for i in range(slow, len(prices) + 1):
            if i >= slow:
                ef = TechnicalIndicators.calculate_ema(prices[:i], fast)
                es = TechnicalIndicators.calculate_ema(prices[:i], slow)
                if ef is not None and es is not None:
                    macd_values.append(ef - es)
        
        if len(macd_values) >= signal:
            signal_line = TechnicalIndicators.calculate_ema(macd_values, signal)
        else:
            signal_line = macd_line
        
        histogram = macd_line - signal_line if signal_line else 0
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, Optional[float]]:
        """Bollinger Bands"""
        if len(prices) < period:
            return {'upper': None, 'middle': None, 'lower': None, 'bandwidth': None, 'percent_b': None}
        
        sma = TechnicalIndicators.calculate_sma(prices, period)
        std = np.std(prices[-period:])
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        bandwidth = (upper_band - lower_band) / sma if sma else 0
        
        # %B indicator (where price is relative to bands)
        current_price = prices[-1]
        percent_b = (current_price - lower_band) / (upper_band - lower_band) if (upper_band - lower_band) != 0 else 0.5
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band,
            'bandwidth': bandwidth,
            'percent_b': percent_b
        }
    
    @staticmethod
    def calculate_stochastic(prices: List[float], highs: List[float], lows: List[float], k_period: int = 14, d_period: int = 3) -> Dict[str, Optional[float]]:
        """Stochastic Oscillator"""
        if len(prices) < k_period or len(highs) < k_period or len(lows) < k_period:
            return {'k': None, 'd': None}
        
        current_close = prices[-1]
        highest_high = max(highs[-k_period:])
        lowest_low = min(lows[-k_period:])
        
        if highest_high == lowest_low:
            return {'k': None, 'd': None}
        
        k = 100 * ((current_close - lowest_low) / (highest_high - lowest_low))
        
        # Simplified %D (would need historical %K values for accurate calculation)
        d = k  # Placeholder
        
        return {'k': k, 'd': d}
    
    @staticmethod
    def calculate_atr(candles: List[Dict], period: int = 14) -> Optional[float]:
        """Average True Range for volatility"""
        if len(candles) < period + 1:
            return None
        
        tr_values = []
        for i in range(1, len(candles)):
            high = candles[i]['high']
            low = candles[i]['low']
            prev_close = candles[i-1]['close']
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            tr = max(tr1, tr2, tr3)
            tr_values.append(tr)
        
        if len(tr_values) < period:
            return None
        
        return sum(tr_values[-period:]) / period
    
    @staticmethod
    def calculate_volume_profile(volumes: List[float], prices: List[float], bins: int = 10) -> Dict:
        """Volume profile analysis"""
        if len(volumes) < 20 or len(prices) < 20:
            return {'poc': None, 'value_area_high': None, 'value_area_low': None}
        
        # Find Point of Control (price level with highest volume)
        vol_price = list(zip(volumes, prices))
        vol_price.sort(key=lambda x: x[0], reverse=True)
        poc = vol_price[0][1] if vol_price else None
        
        # Calculate value area (approximate 70% of volume)
        sorted_by_price = sorted(zip(prices, volumes), key=lambda x: x[0])
        total_vol = sum(volumes)
        target_vol = total_vol * 0.7
        
        current_vol = 0
        value_prices = []
        for price, vol in sorted_by_price:
            if current_vol < target_vol:
                value_prices.append(price)
                current_vol += vol
        
        return {
            'poc': poc,
            'value_area_high': max(value_prices) if value_prices else None,
            'value_area_low': min(value_prices) if value_prices else None
        }


class PriceMonitor:
    """Enhanced price monitoring with multiple data sources"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.price_cache = {}
        self.klines_cache = {}
        self.last_update = None
        self.request_count = 0
        self.error_count = 0
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        try:
            endpoint = f"{self.base_url}/api/v3/ticker/price"
            response = requests.get(endpoint, params={"symbol": symbol}, timeout=10)
            self.request_count += 1
            
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
                self.error_count += 1
                return None
                
        except Exception as e:
            logger.error(f"Exception fetching price for {symbol}: {e}")
            self.error_count += 1
            return None
    
    def get_klines(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[Dict]:
        """Get candlestick data"""
        try:
            endpoint = f"{self.base_url}/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = requests.get(endpoint, params=params, timeout=10)
            self.request_count += 1
            
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
                        'volume': float(item[5]),
                        'close_time': item[6],
                        'quote_volume': float(item[7])
                    })
                
                self.klines_cache[symbol] = {
                    'candles': candles,
                    'timestamp': datetime.now()
                }
                return candles
            else:
                logger.error(f"Error fetching klines for {symbol}: {response.status_code}")
                self.error_count += 1
                return []
                
        except Exception as e:
            logger.error(f"Exception fetching klines for {symbol}: {e}")
            self.error_count += 1
            return []
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get prices for multiple symbols at once"""
        try:
            endpoint = f"{self.base_url}/api/v3/ticker/price"
            response = requests.get(endpoint, timeout=10)
            self.request_count += 1
            
            if response.status_code == 200:
                data = response.json()
                prices = {}
                for item in data:
                    if item['symbol'] in symbols:
                        prices[item['symbol']] = float(item['price'])
                return prices
            return {}
        except Exception as e:
            logger.error(f"Error fetching multiple prices: {e}")
            self.error_count += 1
            return {}
    
    def get_stats(self) -> Dict:
        """Get monitoring statistics"""
        return {
            'requests': self.request_count,
            'errors': self.error_count,
            'error_rate': (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        }


class SignalGenerator:
    """Advanced signal generation with multi-indicator confirmation"""
    
    def __init__(self):
        self.signals_history = deque(maxlen=100)
        self.indicators = TechnicalIndicators()
    
    def detect_volume_spike(self, volumes: List[float], threshold: float = 2.0) -> Tuple[bool, float]:
        """Detect if current volume is spiking"""
        if len(volumes) < 20:
            return False, 1.0
        
        avg_volume = sum(volumes[-20:-1]) / 19
        current_volume = volumes[-1]
        
        ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        return ratio > threshold, ratio
    
    def calculate_trend_strength(self, candles: List[Dict]) -> Dict:
        """Calculate trend strength using multiple indicators"""
        if len(candles) < 50:
            return {'strength': 0, 'direction': 'NEUTRAL'}
        
        closes = [c['close'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        
        # Multiple timeframe trend analysis
        sma_10 = self.indicators.calculate_sma(closes, 10)
        sma_20 = self.indicators.calculate_sma(closes, 20)
        sma_50 = self.indicators.calculate_sma(closes, 50)
        
        trend_score = 0
        
        if sma_10 and sma_20 and sma_50:
            if sma_10 > sma_20 > sma_50:
                trend_score = 1
            elif sma_10 < sma_20 < sma_50:
                trend_score = -1
        
        return {
            'strength': abs(trend_score),
            'direction': 'UP' if trend_score > 0 else 'DOWN' if trend_score < 0 else 'NEUTRAL',
            'sma_10': sma_10,
            'sma_20': sma_20,
            'sma_50': sma_50
        }
    
    def generate_signal(self, candles: List[Dict], symbol: str = "") -> Signal:
        """Generate trading signal with comprehensive indicator analysis"""
        signal = Signal(symbol=symbol, timestamp=datetime.now().isoformat())
        
        if len(candles) < 50:
            signal.reason = 'Insufficient data (need 50+ candles)'
            return signal
        
        closes = [c['close'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        volumes = [c['volume'] for c in candles]
        
        current_price = closes[-1]
        
        # Calculate all indicators
        sma_10 = self.indicators.calculate_sma(closes, 10)
        sma_20 = self.indicators.calculate_sma(closes, 20)
        sma_50 = self.indicators.calculate_sma(closes, 50)
        ema_12 = self.indicators.calculate_ema(closes, 12)
        ema_26 = self.indicators.calculate_ema(closes, 26)
        rsi = self.indicators.calculate_rsi(closes, 14)
        macd = self.indicators.calculate_macd(closes)
        bb = self.indicators.calculate_bollinger_bands(closes)
        stochastic = self.indicators.calculate_stochastic(closes, highs, lows)
        atr = self.indicators.calculate_atr(candles)
        volume_spike, volume_ratio = self.detect_volume_spike(volumes)
        trend = self.calculate_trend_strength(candles)
        
        # Store indicators in signal
        signal.indicators = {
            'price': current_price,
            'sma_10': sma_10,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'ema_12': ema_12,
            'ema_26': ema_26,
            'rsi': rsi,
            'macd': macd,
            'bollinger_bands': bb,
            'stochastic': stochastic,
            'atr': atr,
            'volume_spike': volume_spike,
            'volume_ratio': volume_ratio,
            'trend': trend
        }
        
        # Scoring system for signal generation
        buy_score = 0
        sell_score = 0
        reasons = []
        
        # 1. Trend Analysis (weight: 2)
        if trend['direction'] == 'UP':
            buy_score += 2
            reasons.append('Uptrend confirmed')
        elif trend['direction'] == 'DOWN':
            sell_score += 2
            reasons.append('Downtrend confirmed')
        
        # 2. RSI Analysis (weight: 2)
        if rsi is not None:
            if rsi < 30:
                buy_score += 2
                reasons.append(f'RSI oversold ({rsi:.1f})')
            elif rsi > 70:
                sell_score += 2
                reasons.append(f'RSI overbought ({rsi:.1f})')
            elif 40 < rsi < 60:
                buy_score += 0.5
                sell_score += 0.5
        
        # 3. MACD Analysis (weight: 2)
        if macd['macd'] is not None and macd['signal'] is not None:
            if macd['macd'] > macd['signal'] and macd['histogram'] > 0:
                buy_score += 2
                reasons.append('MACD bullish crossover')
            elif macd['macd'] < macd['signal'] and macd['histogram'] < 0:
                sell_score += 2
                reasons.append('MACD bearish crossover')
        
        # 4. Bollinger Bands Analysis (weight: 1.5)
        if bb['percent_b'] is not None:
            if bb['percent_b'] < 0.1:
                buy_score += 1.5
                reasons.append('Price near lower BB')
            elif bb['percent_b'] > 0.9:
                sell_score += 1.5
                reasons.append('Price near upper BB')
        
        # 5. Volume Analysis (weight: 1.5)
        if volume_spike:
            if trend['direction'] == 'UP':
                buy_score += 1.5
                reasons.append('Volume spike with uptrend')
            elif trend['direction'] == 'DOWN':
                sell_score += 1.5
                reasons.append('Volume spike with downtrend')
        
        # 6. Stochastic Analysis (weight: 1)
        if stochastic['k'] is not None:
            if stochastic['k'] < 20:
                buy_score += 1
                reasons.append('Stochastic oversold')
            elif stochastic['k'] > 80:
                sell_score += 1
                reasons.append('Stochastic overbought')
        
        # 7. EMA Crossover (weight: 1)
        if ema_12 is not None and ema_26 is not None:
            if ema_12 > ema_26:
                buy_score += 1
            else:
                sell_score += 1
        
        # Determine final signal
        total_weight = 11  # Sum of all weights
        buy_confidence = buy_score / total_weight
        sell_confidence = sell_score / total_weight
        
        if buy_confidence >= 0.6 and buy_confidence > sell_confidence:
            signal.signal = 'BUY'
            signal.confidence = min(buy_confidence, 1.0)
            signal.reason = ' | '.join(reasons[:3]) if reasons else 'Multiple bullish indicators'
        elif sell_confidence >= 0.6 and sell_confidence > buy_confidence:
            signal.signal = 'SELL'
            signal.confidence = min(sell_confidence, 1.0)
            signal.reason = ' | '.join(reasons[:3]) if reasons else 'Multiple bearish indicators'
        else:
            signal.signal = 'HOLD'
            signal.confidence = max(buy_confidence, sell_confidence)
            signal.reason = 'No clear signal - mixed indicators'
        
        self.signals_history.append(signal)
        return signal
    
    def get_signal_stats(self) -> Dict:
        """Get statistics on generated signals"""
        if not self.signals_history:
            return {}
        
        total = len(self.signals_history)
        buys = sum(1 for s in self.signals_history if s.signal == 'BUY')
        sells = sum(1 for s in self.signals_history if s.signal == 'SELL')
        holds = sum(1 for s in self.signals_history if s.signal == 'HOLD')
        
        return {
            'total': total,
            'buys': buys,
            'sells': sells,
            'holds': holds,
            'avg_confidence': sum(s.confidence for s in self.signals_history) / total
        }


class RiskManager:
    """Enhanced risk management with dynamic position sizing"""
    
    def __init__(self, 
                 max_daily_loss_pct: float = 3.0,
                 max_position_pct: float = 5.0,
                 max_trades_per_day: int = 10,
                 atr_multiplier_sl: float = 2.0,
                 risk_reward_ratio: float = 2.0):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_position_pct = max_position_pct
        self.max_trades_per_day = max_trades_per_day
        self.atr_multiplier_sl = atr_multiplier_sl
        self.risk_reward_ratio = risk_reward_ratio
        
        self.daily_stats = {
            'loss': 0.0,
            'loss_pct': 0.0,
            'trades': 0,
            'wins': 0,
            'losses': 0
        }
        self.last_reset = datetime.now().date()
        self.trade_history = deque(maxlen=100)
    
    def check_daily_reset(self):
        """Reset daily counters"""
        today = datetime.now().date()
        if today != self.last_reset:
            self.daily_stats = {
                'loss': 0.0,
                'loss_pct': 0.0,
                'trades': 0,
                'wins': 0,
                'losses': 0
            }
            self.last_reset = today
            logger.info("Daily risk counters reset")
    
    def can_trade(self, portfolio_value: float) -> Tuple[bool, str]:
        """Check if trading is allowed based on risk limits"""
        self.check_daily_reset()
        
        if self.daily_stats['loss_pct'] >= self.max_daily_loss_pct:
            return False, f"Daily loss limit reached: {self.daily_stats['loss_pct']:.2f}%"
        
        if self.daily_stats['trades'] >= self.max_trades_per_day:
            return False, f"Max trades per day reached: {self.max_trades_per_day}"
        
        return True, "Trading allowed"
    
    def calculate_dynamic_position_size(self, portfolio_value: float, entry_price: float, 
                                        atr: Optional[float] = None, confidence: float = 0.5) -> Tuple[float, float]:
        """Calculate position size based on risk and volatility"""
        # Base position size
        base_position_pct = self.max_position_pct * confidence
        
        # Adjust for volatility (reduce size if high volatility)
        volatility_factor = 1.0
        if atr and entry_price > 0:
            volatility_pct = (atr / entry_price) * 100
            if volatility_pct > 5:
                volatility_factor = 0.5
            elif volatility_pct > 3:
                volatility_factor = 0.75
        
        adjusted_position_pct = base_position_pct * volatility_factor
        position_value = portfolio_value * (adjusted_position_pct / 100)
        quantity = position_value / entry_price if entry_price > 0 else 0
        
        return round(quantity, 6), adjusted_position_pct
    
    def calculate_stop_loss(self, entry_price: float, side: str, atr: Optional[float] = None) -> float:
        """Calculate stop loss price using ATR-based dynamic stops"""
        if atr:
            stop_distance = atr * self.atr_multiplier_sl
        else:
            stop_distance = entry_price * 0.01  # Default 1%
        
        if side == 'BUY':
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance
    
    def calculate_take_profit(self, entry_price: float, side: str, stop_loss: float) -> float:
        """Calculate take profit based on risk:reward ratio"""
        risk_distance = abs(entry_price - stop_loss)
        reward_distance = risk_distance * self.risk_reward_ratio
        
        if side == 'BUY':
            return entry_price + reward_distance
        else:
            return entry_price - reward_distance
    
    def update_after_trade(self, trade_pnl: float, portfolio_value: float):
        """Update risk metrics after a trade closes"""
        if trade_pnl < 0:
            self.daily_stats['loss'] += abs(trade_pnl)
            self.daily_stats['losses'] += 1
        else:
            self.daily_stats['wins'] += 1
        
        self.daily_stats['loss_pct'] = (self.daily_stats['loss'] / portfolio_value) * 100 if portfolio_value > 0 else 0
        self.daily_stats['trades'] += 1
        
        self.trade_history.append({
            'pnl': trade_pnl,
            'time': datetime.now().isoformat()
        })
    
    def get_stats(self) -> Dict:
        """Get risk management statistics"""
        self.check_daily_reset()
        
        total_closed = self.daily_stats['wins'] + self.daily_stats['losses']
        win_rate = (self.daily_stats['wins'] / total_closed * 100) if total_closed > 0 else 0
        
        return {
            'daily_loss': self.daily_stats['loss'],
            'daily_loss_pct': self.daily_stats['loss_pct'],
            'daily_trades': self.daily_stats['trades'],
            'daily_wins': self.daily_stats['wins'],
            'daily_losses': self.daily_stats['losses'],
            'daily_win_rate': win_rate,
            'remaining_trades': self.max_trades_per_day - self.daily_stats['trades'],
            'max_daily_loss_pct': self.max_daily_loss_pct
        }


class PaperTrader:
    """Enhanced paper trading with comprehensive tracking"""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.peak_balance = initial_balance
        self.open_trades: List[Trade] = []
        self.trade_history: List[Trade] = []
        self.trade_id_counter = 0
        self.equity_curve = deque(maxlen=1000)
        
        # Setup database
        self.db_path = Path('paper_trades.db')
        self.setup_database()
        
        # Track performance
        self.total_fees = 0.0
        self.fee_rate = 0.001  # 0.1% trading fee (typical for Binance)
    
    def setup_database(self):
        """Setup SQLite database for trade tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trades table
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
                strategy TEXT,
                stop_loss REAL,
                take_profit REAL
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance (
                timestamp TEXT PRIMARY KEY,
                balance REAL,
                equity REAL,
                open_trades INTEGER,
                total_trades INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def open_trade(self, symbol: str, side: str, price: float, quantity: float, 
                   stop_loss: float, take_profit: float, strategy: str = "micro_scalp") -> Optional[Trade]:
        """Open a new paper trade"""
        trade_cost = price * quantity
        fee = trade_cost * self.fee_rate
        total_cost = trade_cost + fee
        
        if total_cost > self.balance * 0.95:
            logger.warning(f"Insufficient balance for trade. Required: ${total_cost:.2f}, Available: ${self.balance:.2f}")
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
            strategy=strategy,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.open_trades.append(trade)
        self.balance -= total_cost
        self.total_fees += fee
        
        logger.info(f"OPENED {side} trade #{trade.id}: {symbol} @ ${price:.2f} x {quantity} (SL: ${stop_loss:.2f}, TP: ${take_profit:.2f})")
        
        self.save_trade(trade)
        return trade
    
    def close_trade(self, trade_id: int, exit_price: float, reason: str = "manual") -> Optional[Trade]:
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
        
        # Subtract exit fee
        exit_fee = (exit_price * trade.quantity) * self.fee_rate
        trade.profit_loss -= exit_fee
        self.total_fees += exit_fee
        
        trade.profit_loss_pct = (trade.profit_loss / (trade.entry_price * trade.quantity)) * 100
        
        # Update balance
        self.balance += (exit_price * trade.quantity)
        
        # Move to history
        self.open_trades.remove(trade)
        self.trade_history.append(trade)
        
        # Update peak balance
        current_equity = self.get_equity()
        if current_equity > self.peak_balance:
            self.peak_balance = current_equity
        
        logger.info(f"CLOSED trade #{trade_id}: P&L = ${trade.profit_loss:.2f} ({trade.profit_loss_pct:.2f}%) [{reason}]")
        
        self.update_trade(trade)
        self.record_performance()
        
        return trade
    
    def save_trade(self, trade: Trade):
        """Save trade to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.id, trade.symbol, trade.side, trade.entry_price, trade.exit_price,
            trade.quantity, trade.profit_loss, trade.profit_loss_pct,
            trade.entry_time, trade.exit_time, trade.status, trade.strategy,
            trade.stop_loss, trade.take_profit
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
    
    def record_performance(self):
        """Record performance snapshot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO performance VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            self.balance,
            self.get_equity(),
            len(self.open_trades),
            len(self.trade_history)
        ))
        
        conn.commit()
        conn.close()
    
    def get_equity(self) -> float:
        """Calculate total equity (balance + open positions)"""
        open_value = sum(t.entry_price * t.quantity for t in self.open_trades)
        return self.balance + open_value
    
    def get_stats(self) -> Dict:
        """Get comprehensive trading statistics"""
        closed_trades = [t for t in self.trade_history if t.status == 'CLOSED']
        
        if not closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_profit': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'balance': self.balance,
                'equity': self.get_equity(),
                'total_return_pct': 0,
                'open_trades': len(self.open_trades),
                'total_fees': self.total_fees
            }
        
        winning = [t for t in closed_trades if t.profit_loss > 0]
        losing = [t for t in closed_trades if t.profit_loss <= 0]
        
        total_pnl = sum(t.profit_loss for t in closed_trades)
        total_wins = sum(t.profit_loss for t in winning)
        total_losses = abs(sum(t.profit_loss for t in losing))
        
        avg_profit = sum(t.profit_loss for t in winning) / len(winning) if winning else 0
        avg_loss = sum(t.profit_loss for t in losing) / len(losing) if losing else 0
        
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Calculate max drawdown
        equity_values = [self.initial_balance]
        running_pnl = 0
        for t in closed_trades:
            running_pnl += t.profit_loss
            equity_values.append(self.initial_balance + running_pnl)
        
        max_dd = 0
        peak = equity_values[0]
        for equity in equity_values:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
        
        # Calculate returns for Sharpe ratio (simplified)
        returns = [t.profit_loss_pct for t in closed_trades]
        avg_return = np.mean(returns) if returns else 0
        std_return = np.std(returns) if returns else 1
        sharpe = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0  # Annualized
        
        return {
            'total_trades': len(closed_trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': (len(winning) / len(closed_trades)) * 100,
            'total_pnl': total_pnl,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown_pct': max_dd * 100,
            'sharpe_ratio': sharpe,
            'balance': self.balance,
            'equity': self.get_equity(),
            'total_return_pct': ((self.get_equity() - self.initial_balance) / self.initial_balance) * 100,
            'open_trades': len(self.open_trades),
            'total_fees': self.total_fees
        }


class Backtester:
    """Backtesting engine for strategy validation"""
    
    def __init__(self, signal_generator: SignalGenerator, risk_manager: RiskManager):
        self.signal_generator = signal_generator
        self.risk_manager = risk_manager
        self.results = {}
    
    def run_backtest(self, candles: List[Dict], symbol: str, 
                     initial_balance: float = 10000.0) -> Dict:
        """Run backtest on historical data"""
        logger.info(f"Starting backtest for {symbol} with {len(candles)} candles")
        
        balance = initial_balance
        trades = []
        equity_curve = []
        
        # We need at least 50 candles for indicators
        lookback = 50
        
        for i in range(lookback, len(candles)):
            # Get historical window
            window = candles[i-lookback:i+1]
            current_price = candles[i]['close']
            
            # Generate signal
            signal = self.signal_generator.generate_signal(window, symbol)
            
            # Record equity
            equity_curve.append(balance)
            
            # Simulate trade execution
            if signal.signal == 'BUY' and signal.confidence >= 0.6:
                # Calculate position
                position_value = balance * 0.05  # 5% position
                quantity = position_value / current_price
                
                # Look ahead to find exit (simplified - use next 10 candles)
                exit_idx = min(i + 10, len(candles) - 1)
                exit_price = candles[exit_idx]['close']
                
                # Calculate P&L
                pnl = (exit_price - current_price) * quantity
                pnl_pct = ((exit_price - current_price) / current_price) * 100
                
                trades.append({
                    'entry_price': current_price,
                    'exit_price': exit_price,
                    'quantity': quantity,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'signal_confidence': signal.confidence,
                    'timestamp': candles[i]['timestamp']
                })
                
                balance += pnl
        
        # Calculate metrics
        if trades:
            winning_trades = [t for t in trades if t['pnl'] > 0]
            losing_trades = [t for t in trades if t['pnl'] <= 0]
            
            total_return = ((balance - initial_balance) / initial_balance) * 100
            win_rate = (len(winning_trades) / len(trades)) * 100
            
            max_drawdown = 0
            peak = initial_balance
            for equity in equity_curve:
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak
                if dd > max_dd:
                    max_dd = dd
            
            self.results = {
                'symbol': symbol,
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'initial_balance': initial_balance,
                'final_balance': balance,
                'total_return_pct': total_return,
                'max_drawdown_pct': max_dd * 100,
                'trades': trades
            }
        else:
            self.results = {
                'symbol': symbol,
                'total_trades': 0,
                'message': 'No trades generated during backtest'
            }
        
        return self.results
    
    def print_report(self):
        """Print backtest report"""
        if not self.results:
            print("No backtest results available")
            return
        
        print("\n" + "="*60)
        print("BACKTEST REPORT")
        print("="*60)
        print(f"Symbol: {self.results.get('symbol', 'N/A')}")
        print(f"Total Trades: {self.results.get('total_trades', 0)}")
        print(f"Win Rate: {self.results.get('win_rate', 0):.1f}%")
        print(f"Total Return: {self.results.get('total_return_pct', 0):.2f}%")
        print(f"Max Drawdown: {self.results.get('max_drawdown_pct', 0):.2f}%")
        print("="*60)


class DashboardServer:
    """Simple web dashboard for monitoring"""
    
    def __init__(self, bot, host='localhost', port=8080):
        self.bot = bot
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
    
    def generate_html(self) -> str:
        """Generate dashboard HTML"""
        stats = self.bot.trader.get_stats()
        risk_stats = self.bot.risk_manager.get_stats()
        signal_stats = self.bot.signal_generator.get_signal_stats()
        monitor_stats = self.bot.price_monitor.get_stats()
        
        open_trades_html = ""
        for trade in self.bot.trader.open_trades:
            current_price = self.bot.price_monitor.get_price(trade.symbol)
            if current_price:
                pnl = (current_price - trade.entry_price) * trade.quantity
                pnl_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
                open_trades_html += f"""
                <tr>
                    <td>{trade.symbol}</td>
                    <td>{trade.side}</td>
                    <td>${trade.entry_price:.2f}</td>
                    <td>${current_price:.2f}</td>
                    <td class="{'positive' if pnl > 0 else 'negative'}">${pnl:.2f} ({pnl_pct:+.2f}%)</td>
                    <td>${trade.stop_loss:.2f} / ${trade.take_profit:.2f}</td>
                </tr>
                """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Micro-Scalp Bot Dashboard</title>
            <meta http-equiv="refresh" content="10">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a2e; color: #eee; }}
                h1 {{ color: #00d4aa; }}
                h2 {{ color: #00d4aa; border-bottom: 2px solid #00d4aa; padding-bottom: 10px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
                .card {{ background: #16213e; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
                .metric {{ font-size: 2em; font-weight: bold; color: #00d4aa; }}
                .label {{ color: #888; font-size: 0.9em; }}
                .positive {{ color: #00d4aa; }}
                .negative {{ color: #ff4757; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333; }}
                th {{ background: #0f3460; }}
                tr:hover {{ background: #1a1a2e; }}
                .status {{ padding: 5px 10px; border-radius: 5px; background: #0f3460; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Micro-Scalp Trading Bot Dashboard</h1>
                <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="grid">
                    <div class="card">
                        <div class="label">Balance</div>
                        <div class="metric">${stats.get('balance', 0):,.2f}</div>
                    </div>
                    <div class="card">
                        <div class="label">Equity</div>
                        <div class="metric">${stats.get('equity', 0):,.2f}</div>
                    </div>
                    <div class="card">
                        <div class="label">Total Return</div>
                        <div class="metric {'positive' if stats.get('total_return_pct', 0) > 0 else 'negative'}">{stats.get('total_return_pct', 0):+.2f}%</div>
                    </div>
                    <div class="card">
                        <div class="label">Win Rate</div>
                        <div class="metric">{stats.get('win_rate', 0):.1f}%</div>
                    </div>
                    <div class="card">
                        <div class="label">Total Trades</div>
                        <div class="metric">{stats.get('total_trades', 0)}</div>
                    </div>
                    <div class="card">
                        <div class="label">Open Trades</div>
                        <div class="metric">{stats.get('open_trades', 0)}</div>
                    </div>
                    <div class="card">
                        <div class="label">Max Drawdown</div>
                        <div class="metric negative">{stats.get('max_drawdown_pct', 0):.2f}%</div>
                    </div>
                    <div class="card">
                        <div class="label">Profit Factor</div>
                        <div class="metric">{stats.get('profit_factor', 0):.2f}</div>
                    </div>
                </div>
                
                <h2>Open Trades</h2>
                <table>
                    <tr>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Entry</th>
                        <th>Current</th>
                        <th>Unrealized P&L</th>
                        <th>SL / TP</th>
                    </tr>
                    {open_trades_html if open_trades_html else '<tr><td colspan="6" style="text-align:center">No open trades</td></tr>'}
                </table>
                
                <h2>Risk Status</h2>
                <div class="grid">
                    <div class="card">
                        <div class="label">Daily Loss</div>
                        <div class="metric {'negative' if risk_stats.get('daily_loss_pct', 0) > 1 else ''}">{risk_stats.get('daily_loss_pct', 0):.2f}%</div>
                    </div>
                    <div class="card">
                        <div class="label">Trades Today</div>
                        <div class="metric">{risk_stats.get('daily_trades', 0)} / {self.bot.risk_manager.max_trades_per_day}</div>
                    </div>
                    <div class="card">
                        <div class="label">Remaining Trades</div>
                        <div class="metric">{risk_stats.get('remaining_trades', 0)}</div>
                    </div>
                </div>
                
                <h2>Signals</h2>
                <div class="grid">
                    <div class="card">
                        <div class="label">Buy Signals</div>
                        <div class="metric positive">{signal_stats.get('buys', 0)}</div>
                    </div>
                    <div class="card">
                        <div class="label">Sell Signals</div>
                        <div class="metric negative">{signal_stats.get('sells', 0)}</div>
                    </div>
                    <div class="card">
                        <div class="label">Avg Confidence</div>
                        <div class="metric">{signal_stats.get('avg_confidence', 0):.2f}</div>
                    </div>
                </div>
                
                <h2>API Health</h2>
                <div class="grid">
                    <div class="card">
                        <div class="label">Requests</div>
                        <div class="metric">{monitor_stats.get('requests', 0)}</div>
                    </div>
                    <div class="card">
                        <div class="label">Errors</div>
                        <div class="metric {'negative' if monitor_stats.get('error_rate', 0) > 5 else ''}">{monitor_stats.get('errors', 0)}</div>
                    </div>
                    <div class="card">
                        <div class="label">Error Rate</div>
                        <div class="metric">{monitor_stats.get('error_rate', 0):.2f}%</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def start(self):
        """Start dashboard server in background thread"""
        handler = self.create_handler()
        self.server = HTTPServer((self.host, self.port), handler)
        
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        
        logger.info(f"Dashboard running at http://{self.host}:{self.port}")
    
    def create_handler(self):
        """Create request handler class"""
        dashboard = self
        
        class DashboardHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/' or self.path == '/dashboard':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(dashboard.generate_html().encode())
                elif self.path == '/api/stats':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    stats = {
                        'trader': dashboard.bot.trader.get_stats(),
                        'risk': dashboard.bot.risk_manager.get_stats(),
                        'signals': dashboard.bot.signal_generator.get_signal_stats(),
                        'monitor': dashboard.bot.price_monitor.get_stats()
                    }
                    self.wfile.write(json.dumps(stats).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass  # Suppress logging
        
        return DashboardHandler
    
    def stop(self):
        """Stop dashboard server"""
        if self.server:
            self.server.shutdown()
            logger.info("Dashboard stopped")


class MicroScalpBot:
    """Enhanced main trading bot"""
    
    def __init__(self, symbols: List[str] = None, enable_dashboard: bool = True):
        self.symbols = symbols or ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        self.price_monitor = PriceMonitor()
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager()
        self.trader = PaperTrader(initial_balance=10000.0)
        self.backtester = Backtester(self.signal_generator, self.risk_manager)
        
        self.running = False
        self.check_interval = 60
        self.dashboard = None
        self.enable_dashboard = enable_dashboard
        
        # Performance tracking
        self.loop_count = 0
        self.start_time = None
    
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
            if trade.side == 'BUY':
                if current_price <= trade.stop_loss:
                    logger.info(f"STOP LOSS triggered for {trade.symbol}")
                    closed_trade = self.trader.close_trade(trade.id, current_price, "stop_loss")
                    if closed_trade:
                        self.risk_manager.update_after_trade(closed_trade.profit_loss, self.trader.get_equity())
                elif current_price >= trade.take_profit:
                    logger.info(f"TAKE PROFIT triggered for {trade.symbol}")
                    closed_trade = self.trader.close_trade(trade.id, current_price, "take_profit")
                    if closed_trade:
                        self.risk_manager.update_after_trade(closed_trade.profit_loss, self.trader.get_equity())
    
    def check_new_signals(self):
        """Check for new trading signals"""
        can_trade, reason = self.risk_manager.can_trade(self.trader.get_equity())
        if not can_trade:
            if self.loop_count % 10 == 0:  # Log only every 10 loops to avoid spam
                logger.warning(f"Trading blocked: {reason}")
            return
        
        for symbol in self.symbols:
            # Skip if already have open trade for this symbol
            if any(t.symbol == symbol for t in self.trader.open_trades):
                continue
            
            # Get price data
            candles = self.price_monitor.get_klines(symbol, interval='5m', limit=100)
            if not candles or len(candles) < 50:
                continue
            
            # Generate signal
            signal = self.signal_generator.generate_signal(candles, symbol)
            
            if signal.signal == 'BUY' and signal.confidence >= 0.6:
                logger.info(f"BUY signal for {symbol}: {signal.reason} (confidence: {signal.confidence:.2f})")
                
                current_price = signal.indicators['price']
                atr = signal.indicators.get('atr')
                
                # Calculate position size
                quantity, position_pct = self.risk_manager.calculate_dynamic_position_size(
                    self.trader.get_equity(), current_price, atr, signal.confidence
                )
                
                # Calculate stop loss and take profit
                stop_loss = self.risk_manager.calculate_stop_loss(current_price, 'BUY', atr)
                take_profit = self.risk_manager.calculate_take_profit(current_price, 'BUY', stop_loss)
                
                # Open trade
                trade = self.trader.open_trade(symbol, 'BUY', current_price, quantity, stop_loss, take_profit)
                if trade:
                    self.risk_manager.daily_stats['trades'] += 1
    
    def print_status(self):
        """Print current bot status"""
        stats = self.trader.get_stats()
        risk_stats = self.risk_manager.get_stats()
        
        print("\n" + "="*70)
        print("MICRO-SCALP BOT STATUS v2.0")
        print("="*70)
        print(f"Balance:        ${stats['balance']:,.2f}")
        print(f"Equity:         ${stats['equity']:,.2f}")
        print(f"Total Return:   {stats['total_return_pct']:+.2f}%")
        print(f"Win Rate:       {stats['win_rate']:.1f}%")
        print(f"Total Trades:   {stats['total_trades']}")
        print(f"Open Trades:    {stats['open_trades']}")
        print(f"Max Drawdown:   {stats['max_drawdown_pct']:.2f}%")
        print(f"Daily Loss:     {risk_stats['daily_loss_pct']:.2f}%")
        print("="*70)
        
        if self.trader.open_trades:
            print("\nOPEN TRADES:")
            for trade in self.trader.open_trades:
                current_price = self.price_monitor.get_price(trade.symbol)
                if current_price:
                    pnl = (current_price - trade.entry_price) * trade.quantity
                    pnl_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
                    print(f"  {trade.symbol}: ${trade.entry_price:.2f} -> ${current_price:.2f} | P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        
        print("")
    
    def run_backtest(self, symbol: str = 'BTCUSDT', days: int = 30):
        """Run backtest for a symbol"""
        print(f"\nRunning backtest for {symbol} (last {days} days)...")
        
        # Get historical data
        candles = self.price_monitor.get_klines(symbol, interval='1h', limit=days*24)
        
        if not candles or len(candles) < 50:
            print(f"Insufficient data for backtest. Got {len(candles) if candles else 0} candles.")
            return
        
        results = self.backtester.run_backtest(candles, symbol)
        self.backtester.print_report()
        
        return results
    
    def run(self):
        """Main bot loop"""
        logger.info("="*70)
        logger.info("Starting Micro-Scalp Bot v2.0 (PAPER TRADING MODE)")
        logger.info("="*70)
        logger.info(f"Symbols: {self.symbols}")
        logger.info(f"Initial Balance: ${self.trader.initial_balance:,.2f}")
        logger.info(f"Check Interval: {self.check_interval}s")
        
        # Start dashboard
        if self.enable_dashboard:
            self.dashboard = DashboardServer(self)
            self.dashboard.start()
            print(f"\nDashboard available at: http://localhost:8080")
        
        self.running = True
        self.start_time = datetime.now()
        
        try:
            while self.running:
                self.loop_count += 1
                
                # Check existing trades
                self.check_open_trades()
                
                # Check for new signals
                self.check_new_signals()
                
                # Print status every 5 loops
                if self.loop_count % 5 == 0:
                    self.print_status()
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"Bot error: {e}", exc_info=True)
            self.running = False
        finally:
            if self.dashboard:
                self.dashboard.stop()
            
            # Final stats
            print("\n" + "="*70)
            print("FINAL STATISTICS")
            print("="*70)
            self.print_status()


def main():
    """Entry point"""
    print("="*70)
    print("MICRO-SCALP TRADING BOT v2.0")
    print("="*70)
    print("PAPER TRADING MODE - NO REAL MONEY")
    print("="*70)
    print()
    print("Features:")
    print("  - RSI, MACD, Bollinger Bands, Stochastic indicators")
    print("  - Dynamic position sizing with ATR-based stops")
    print("  - Backtesting capability")
    print("  - Web dashboard at http://localhost:8080")
    print("  - Comprehensive risk management")
    print()
    
    # Create bot
    bot = MicroScalpBot(
        symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT'],
        enable_dashboard=True
    )
    
    # Optionally run backtest first
    # bot.run_backtest('BTCUSDT', days=30)
    
    # Run live paper trading
    bot.run()


if __name__ == "__main__":
    main()
