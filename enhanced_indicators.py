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
        """Analyze all technical indicators and generate comprehensive signals"""
        
        if len(data) < 200:  # Need sufficient data for all indicators
            return {
                'symbol': symbol,
                'signal': 'INSUFFICIENT_DATA',
                'strength': 0,
                'details': 'Need at least 200 data points for comprehensive analysis'
            }
        
        # Calculate all indicators
        rsi = self.indicators.calculate_rsi(data)
        bollinger = self.indicators.calculate_bollinger_bands(data)
        moving_averages = self.indicators.calculate_moving_averages(data)
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
        
        # Analyze each indicator
        signals = self._analyze_individual_signals(
            data, rsi, bollinger, moving_averages, macd_data, support_resistance,
            current_price, prev_price, current_rsi, prev_rsi,
            current_macd, current_signal, prev_macd, prev_signal
        )
        
        # Calculate overall signal strength
        buy_score = sum([1 for s in signals.values() if s['signal'] == 'BUY'])
        sell_score = sum([1 for s in signals.values() if s['signal'] == 'SELL'])
        neutral_score = sum([1 for s in signals.values() if s['signal'] == 'NEUTRAL'])
        
        total_signals = len(signals)
        
        # Determine overall signal
        overall_signal, signal_strength = self._determine_overall_signal(
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
    
    def _analyze_individual_signals(self, data, rsi, bollinger, moving_averages, macd_data, support_resistance,
                                  current_price, prev_price, current_rsi, prev_rsi,
                                  current_macd, current_signal, prev_macd, prev_signal):
        """Analyze each individual indicator"""
        
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
        
        # 3. Moving Average Analysis
        ma20 = moving_averages['ma_20'].iloc[-1]
        ma50 = moving_averages['ma_50'].iloc[-1]
        
        if current_price > ma20 > ma50:
            signals['MA_Trend'] = {'signal': 'BUY', 'reason': 'Price above MA20 above MA50 (bullish trend)'}
        elif current_price < ma20 < ma50:
            signals['MA_Trend'] = {'signal': 'SELL', 'reason': 'Price below MA20 below MA50 (bearish trend)'}
        else:
            signals['MA_Trend'] = {'signal': 'NEUTRAL', 'reason': 'Mixed moving average signals'}
        
        # 4. Moving Average Crossover
        prev_ma20 = moving_averages['ma_20'].iloc[-2]
        prev_ma50 = moving_averages['ma_50'].iloc[-2]
        
        if ma20 > ma50 and prev_ma20 <= prev_ma50:
            signals['MA_Crossover'] = {'signal': 'BUY', 'reason': 'MA20 crossed above MA50'}
        elif ma20 < ma50 and prev_ma20 >= prev_ma50:
            signals['MA_Crossover'] = {'signal': 'SELL', 'reason': 'MA20 crossed below MA50'}
        else:
            signals['MA_Crossover'] = {'signal': 'NEUTRAL', 'reason': 'No MA crossover'}
        
        # 5. Bollinger Bands Analysis
        upper_band = bollinger['upper_band'].iloc[-1]
        lower_band = bollinger['lower_band'].iloc[-1]
        middle_band = bollinger['middle_band'].iloc[-1]
        
        if current_price <= lower_band:
            signals['Bollinger'] = {'signal': 'BUY', 'reason': 'Price at/below lower Bollinger band'}
        elif current_price >= upper_band:
            signals['Bollinger'] = {'signal': 'SELL', 'reason': 'Price at/above upper Bollinger band'}
        elif current_price > middle_band:
            signals['Bollinger'] = {'signal': 'BUY', 'reason': 'Price above BB middle line'}
        elif current_price < middle_band:
            signals['Bollinger'] = {'signal': 'SELL', 'reason': 'Price below BB middle line'}
        else:
            signals['Bollinger'] = {'signal': 'NEUTRAL', 'reason': 'Price near BB middle'}
        
        # 6. Support/Resistance Analysis
        support = support_resistance['support']
        resistance = support_resistance['resistance']
        
        if current_price > prev_price and current_price > resistance * 0.99:
            signals['Support_Resistance'] = {'signal': 'BUY', 'reason': 'Breaking above resistance'}
        elif current_price < prev_price and current_price < support * 1.01:
            signals['Support_Resistance'] = {'signal': 'SELL', 'reason': 'Breaking below support'}
        elif abs(current_price - support) / support < 0.02:  # Within 2% of support
            signals['Support_Resistance'] = {'signal': 'BUY', 'reason': 'Near support level'}
        elif abs(current_price - resistance) / resistance < 0.02:  # Within 2% of resistance
            signals['Support_Resistance'] = {'signal': 'SELL', 'reason': 'Near resistance level'}
        else:
            signals['Support_Resistance'] = {'signal': 'NEUTRAL', 'reason': 'Between support and resistance'}
        
        return signals
    
    def _determine_overall_signal(self, buy_score, sell_score, neutral_score, total_signals):
        """Determine overall signal based on individual signals"""
        
        buy_percentage = (buy_score / total_signals) * 100
        sell_percentage = (sell_score / total_signals) * 100
        
        if buy_score >= 4:  # Strong buy (4 or more buy signals)
            return 'STRONG_BUY', buy_percentage
        elif buy_score >= 3:  # Moderate buy (3 buy signals)
            return 'BUY', buy_percentage
        elif sell_score >= 4:  # Strong sell (4 or more sell signals)
            return 'STRONG_SELL', sell_percentage
        elif sell_score >= 3:  # Moderate sell (3 sell signals)
            return 'SELL', sell_percentage
        elif buy_score > sell_score:
            return 'WEAK_BUY', buy_percentage
        elif sell_score > buy_score:
            return 'WEAK_SELL', sell_percentage
        else:
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