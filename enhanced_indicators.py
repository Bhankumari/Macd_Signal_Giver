import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any

class TechnicalIndicators:
    """Comprehensive technical indicators for stock analysis"""
    
    @staticmethod
    def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index (RSI)"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = data['close'].rolling(window=period).mean()
        std = data['close'].rolling(window=period).std()
        
        return {
            'upper_band': sma + (std * std_dev),
            'middle_band': sma,
            'lower_band': sma - (std * std_dev)
        }
    
    @staticmethod
    def calculate_moving_averages(data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate various moving averages"""
        return {
            'ma_5': data['close'].rolling(window=5).mean(),
            'ma_10': data['close'].rolling(window=10).mean(),
            'ma_20': data['close'].rolling(window=20).mean(),
            'ma_50': data['close'].rolling(window=50).mean(),
            'ma_100': data['close'].rolling(window=100).mean(),
            'ma_200': data['close'].rolling(window=200).mean()
        }
    
    @staticmethod
    def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Enhanced MACD calculation"""
        exp1 = data['close'].ewm(span=fast).mean()
        exp2 = data['close'].ewm(span=slow).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def find_support_resistance(data: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """Find support and resistance levels"""
        recent_data = data.tail(window * 2)  # Look at more data for better levels
        
        # Find local highs and lows
        highs = recent_data['high'].rolling(window=5, center=True).max()
        lows = recent_data['low'].rolling(window=5, center=True).min()
        
        # Current support/resistance levels
        resistance_levels = []
        support_levels = []
        
        for i in range(len(recent_data)):
            if recent_data['high'].iloc[i] == highs.iloc[i]:
                resistance_levels.append(recent_data['high'].iloc[i])
            if recent_data['low'].iloc[i] == lows.iloc[i]:
                support_levels.append(recent_data['low'].iloc[i])
        
        current_price = data['close'].iloc[-1]
        
        # Find nearest support and resistance
        resistance_levels = [r for r in resistance_levels if r > current_price]
        support_levels = [s for s in support_levels if s < current_price]
        
        return {
            'resistance': min(resistance_levels) if resistance_levels else current_price * 1.05,
            'support': max(support_levels) if support_levels else current_price * 0.95,
            'current_price': current_price
        }

class SignalAnalyzer:
    """Comprehensive signal analysis using multiple indicators"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def analyze_all_signals(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Analyze MACD and RSI indicators only for simplified signal generation"""
        
        if len(data) < 50:  # Need sufficient data for MACD and RSI
            return {
                'symbol': symbol,
                'signal': 'INSUFFICIENT_DATA',
                'strength': 0,
                'details': 'Need at least 50 data points for MACD and RSI analysis'
            }
        
        # Calculate only MACD and RSI indicators
        rsi = self.indicators.calculate_rsi(data)
        macd_data = self.indicators.calculate_macd(data)
        support_resistance = self.indicators.find_support_resistance(data)
        
        # Get latest values
        latest_idx = -1
        prev_idx = -2
        
        current_price = data['close'].iloc[latest_idx]
        prev_price = data['close'].iloc[prev_idx]
        
        current_rsi = rsi.iloc[latest_idx]
        prev_rsi = rsi.iloc[prev_idx]
        
        current_macd = macd_data['macd'].iloc[latest_idx]
        current_signal = macd_data['signal'].iloc[latest_idx]
        prev_macd = macd_data['macd'].iloc[prev_idx]
        prev_signal = macd_data['signal'].iloc[prev_idx]
        
        # Analyze only MACD and RSI indicators
        signals = self._analyze_macd_rsi_only(
            current_rsi, prev_rsi, current_macd, current_signal, prev_macd, prev_signal
        )
        
        # Calculate overall signal strength
        buy_score = sum([1 for s in signals.values() if s['signal'] == 'BUY'])
        sell_score = sum([1 for s in signals.values() if s['signal'] == 'SELL'])
        neutral_score = sum([1 for s in signals.values() if s['signal'] == 'NEUTRAL'])
        
        total_signals = len(signals)
        
        # Determine overall signal (simplified for 2 indicators)
        overall_signal, signal_strength = self._determine_macd_rsi_signal(
            buy_score, sell_score, neutral_score, total_signals
        )
        
        # Calculate stop loss and target prices
        stop_loss, target_price = self._calculate_stop_loss_and_target(
            current_price, overall_signal, support_resistance
        )
        
        return {
            'symbol': symbol,
            'current_price': round(current_price, 2),
            'signal': overall_signal,
            'strength': signal_strength,
            'buy_signals': buy_score,
            'sell_signals': sell_score,
            'neutral_signals': neutral_score,
            'total_indicators': total_signals,
            'individual_signals': signals,
            'stop_loss': stop_loss,
            'target_price': target_price,
            'support': round(support_resistance['support'], 2),
            'resistance': round(support_resistance['resistance'], 2),
            'risk_reward_ratio': round((target_price - current_price) / abs(current_price - stop_loss), 2) if stop_loss != current_price else 0
        }
    
    def _analyze_macd_rsi_only(self, current_rsi, prev_rsi, current_macd, current_signal, prev_macd, prev_signal):
        """Analyze only MACD and RSI indicators"""
        
        signals = {}
        
        # 1. MACD Analysis
        if current_macd > current_signal and prev_macd <= prev_signal:
            signals['MACD'] = {'signal': 'BUY', 'reason': 'MACD bullish crossover'}
        elif current_macd < current_signal and prev_macd >= prev_signal:
            signals['MACD'] = {'signal': 'SELL', 'reason': 'MACD bearish crossover'}
        else:
            signals['MACD'] = {'signal': 'NEUTRAL', 'reason': f'MACD: {round(current_macd, 4)} vs Signal: {round(current_signal, 4)}'}
        
        # 2. RSI Analysis
        if current_rsi < 30:
            signals['RSI'] = {'signal': 'BUY', 'reason': f'RSI oversold ({round(current_rsi, 1)})'}
        elif current_rsi > 70:
            signals['RSI'] = {'signal': 'SELL', 'reason': f'RSI overbought ({round(current_rsi, 1)})'}
        elif current_rsi < 50 and prev_rsi >= 50:
            signals['RSI'] = {'signal': 'SELL', 'reason': f'RSI falling below 50 ({round(current_rsi, 1)})'}
        elif current_rsi > 50 and prev_rsi <= 50:
            signals['RSI'] = {'signal': 'BUY', 'reason': f'RSI rising above 50 ({round(current_rsi, 1)})'}
        else:
            signals['RSI'] = {'signal': 'NEUTRAL', 'reason': f'RSI neutral ({round(current_rsi, 1)})'}
        
        return signals
    
    def _determine_macd_rsi_signal(self, buy_score, sell_score, neutral_score, total_signals):
        """Determine overall signal based on MACD and RSI only (2 indicators)"""
        
        buy_percentage = (buy_score / total_signals) * 100
        sell_percentage = (sell_score / total_signals) * 100
        
        if buy_score == 2:  # Both MACD and RSI are BUY
            return 'STRONG_BUY', buy_percentage
        elif buy_score == 1 and sell_score == 0:  # One BUY, one NEUTRAL
            return 'BUY', buy_percentage
        elif sell_score == 2:  # Both MACD and RSI are SELL
            return 'STRONG_SELL', sell_percentage
        elif sell_score == 1 and buy_score == 0:  # One SELL, one NEUTRAL
            return 'SELL', sell_percentage
        elif buy_score == 1 and sell_score == 1:  # One BUY, one SELL - conflicting signals
            return 'NEUTRAL', 50.0
        else:  # Both NEUTRAL
            return 'NEUTRAL', max(buy_percentage, sell_percentage)
    
    def _calculate_stop_loss_and_target(self, current_price, signal, support_resistance):
        """Calculate stop loss and target price based on signal and support/resistance"""
        
        support = support_resistance['support']
        resistance = support_resistance['resistance']
        
        if signal in ['STRONG_BUY', 'BUY', 'WEAK_BUY']:
            # For buy signals
            stop_loss = max(
                support * 0.98,  # 2% below support
                current_price * 0.95  # 5% below current price
            )
            target_price = min(
                resistance * 1.02,  # 2% above resistance
                current_price * 1.10  # 10% above current price
            )
        elif signal in ['STRONG_SELL', 'SELL', 'WEAK_SELL']:
            # For sell signals (if holding)
            stop_loss = min(
                resistance * 1.02,  # 2% above resistance
                current_price * 1.05  # 5% above current price
            )
            target_price = max(
                support * 0.98,  # 2% below support
                current_price * 0.90  # 10% below current price
            )
        else:
            # Neutral
            stop_loss = current_price * 0.95  # 5% stop loss
            target_price = current_price * 1.05  # 5% target
        
        return round(stop_loss, 2), round(target_price, 2)

def format_telegram_message(analysis: Dict[str, Any]) -> str:
    """Format comprehensive analysis for Telegram message"""
    
    symbol = analysis['symbol']
    signal = analysis['signal']
    strength = analysis['strength']
    current_price = analysis['current_price']
    
    # Signal emoji
    signal_emojis = {
        'STRONG_BUY': '🟢🟢🟢',
        'BUY': '🟢🟢',
        'WEAK_BUY': '🟢',
        'STRONG_SELL': '🔴🔴🔴',
        'SELL': '🔴🔴',
        'WEAK_SELL': '🔴',
        'NEUTRAL': '🟡'
    }
    
    emoji = signal_emojis.get(signal, '⚪')
    
    message = f"""
{emoji} <b>{symbol}</b> - {signal} ({strength:.1f}%)

💰 <b>Price:</b> ₹{current_price}
🎯 <b>Target:</b> ₹{analysis['target_price']}
🛑 <b>Stop Loss:</b> ₹{analysis['stop_loss']}
⚖️ <b>Risk/Reward:</b> 1:{analysis['risk_reward_ratio']}

📊 <b>Support:</b> ₹{analysis['support']} | <b>Resistance:</b> ₹{analysis['resistance']}

📈 <b>Signal Breakdown:</b>
✅ Buy Signals: {analysis['buy_signals']}/{analysis['total_indicators']}
❌ Sell Signals: {analysis['sell_signals']}/{analysis['total_indicators']}
➖ Neutral: {analysis['neutral_signals']}/{analysis['total_indicators']}

🔍 <b>Indicator Details:</b>"""
    
    for indicator, details in analysis['individual_signals'].items():
        signal_icon = '✅' if details['signal'] == 'BUY' else '❌' if details['signal'] == 'SELL' else '➖'
        message += f"\n{signal_icon} <b>{indicator}:</b> {details['reason']}"
    
    # Add trading recommendation
    if signal in ['STRONG_BUY', 'BUY']:
        message += f"\n\n💡 <b>Recommendation:</b> Consider buying near ₹{current_price} with stop loss at ₹{analysis['stop_loss']}"
    elif signal in ['STRONG_SELL', 'SELL']:
        message += f"\n\n💡 <b>Recommendation:</b> Consider selling/avoiding, stop loss at ₹{analysis['stop_loss']}"
    else:
        message += f"\n\n💡 <b>Recommendation:</b> Wait for clearer signals"
    
    return message 