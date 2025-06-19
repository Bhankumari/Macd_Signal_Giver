from typing import Dict, Any

def format_short_message(analysis: Dict[str, Any]) -> str:
    """SHORT message format - just essential info"""
    
    signal_emojis = {
        'STRONG_BUY': '🟢🟢🟢', 'BUY': '🟢🟢', 'WEAK_BUY': '🟢',
        'STRONG_SELL': '🔴🔴🔴', 'SELL': '🔴🔴', 'WEAK_SELL': '🔴',
        'NEUTRAL': '🟡'
    }
    
    emoji = signal_emojis.get(analysis['signal'], '⚪')
    
    return f"""{emoji} <b>{analysis['symbol']}</b> - {analysis['signal']}
💰 ₹{analysis['current_price']} → 🎯 ₹{analysis['target_price']} | 🛑 ₹{analysis['stop_loss']}"""

def format_medium_message(analysis: Dict[str, Any]) -> str:
    """MEDIUM message format - key details only"""
    
    signal_emojis = {
        'STRONG_BUY': '🟢🟢🟢', 'BUY': '🟢🟢', 'WEAK_BUY': '🟢',
        'STRONG_SELL': '🔴🔴🔴', 'SELL': '🔴🔴', 'WEAK_SELL': '🔴',
        'NEUTRAL': '🟡'
    }
    
    emoji = signal_emojis.get(analysis['signal'], '⚪')
    
    return f"""{emoji} <b>{analysis['symbol']}</b> - {analysis['signal']} ({analysis['strength']:.1f}%)

💰 <b>Price:</b> ₹{analysis['current_price']}
🎯 <b>Target:</b> ₹{analysis['target_price']}
🛑 <b>Stop Loss:</b> ₹{analysis['stop_loss']}
⚖️ <b>Risk/Reward:</b> 1:{analysis['risk_reward_ratio']}

📈 <b>Signals:</b> {analysis['buy_signals']} Buy | {analysis['sell_signals']} Sell | {analysis['neutral_signals']} Neutral"""

def format_detailed_message(analysis: Dict[str, Any]) -> str:
    """DETAILED message format - full comprehensive analysis (current default)"""
    
    signal_emojis = {
        'STRONG_BUY': '🟢🟢🟢', 'BUY': '🟢🟢', 'WEAK_BUY': '🟢',
        'STRONG_SELL': '🔴🔴🔴', 'SELL': '🔴🔴', 'WEAK_SELL': '🔴',
        'NEUTRAL': '🟡'
    }
    
    emoji = signal_emojis.get(analysis['signal'], '⚪')
    
    message = f"""{emoji} <b>{analysis['symbol']}</b> - {analysis['signal']} ({analysis['strength']:.1f}%)

💰 <b>Price:</b> ₹{analysis['current_price']}
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
    if analysis['signal'] in ['STRONG_BUY', 'BUY']:
        message += f"\n\n💡 <b>Recommendation:</b> Consider buying near ₹{analysis['current_price']} with stop loss at ₹{analysis['stop_loss']}"
    elif analysis['signal'] in ['STRONG_SELL', 'SELL']:
        message += f"\n\n💡 <b>Recommendation:</b> Consider selling/avoiding, stop loss at ₹{analysis['stop_loss']}"
    else:
        message += f"\n\n💡 <b>Recommendation:</b> Wait for clearer signals"
    
    return message

def format_custom_message(analysis: Dict[str, Any], include_details=True, include_indicators=True, include_recommendation=True) -> str:
    """CUSTOM message format - choose what to include"""
    
    signal_emojis = {
        'STRONG_BUY': '🟢🟢🟢', 'BUY': '🟢🟢', 'WEAK_BUY': '🟢',
        'STRONG_SELL': '🔴🔴🔴', 'SELL': '🔴🔴', 'WEAK_SELL': '🔴',
        'NEUTRAL': '🟡'
    }
    
    emoji = signal_emojis.get(analysis['signal'], '⚪')
    
    # Basic header
    message = f"{emoji} <b>{analysis['symbol']}</b> - {analysis['signal']} ({analysis['strength']:.1f}%)"
    
    # Price info (always included)
    message += f"\n💰 ₹{analysis['current_price']} → 🎯 ₹{analysis['target_price']} | 🛑 ₹{analysis['stop_loss']}"
    
    if include_details:
        message += f"\n⚖️ <b>Risk/Reward:</b> 1:{analysis['risk_reward_ratio']}"
        message += f"\n📊 <b>Support:</b> ₹{analysis['support']} | <b>Resistance:</b> ₹{analysis['resistance']}"
        message += f"\n📈 <b>Signals:</b> {analysis['buy_signals']} Buy | {analysis['sell_signals']} Sell"
    
    if include_indicators:
        message += f"\n\n🔍 <b>Key Indicators:</b>"
        # Show only the most important indicators
        key_indicators = ['MACD', 'RSI', 'MA_Trend']
        for indicator in key_indicators:
            if indicator in analysis['individual_signals']:
                details = analysis['individual_signals'][indicator]
                signal_icon = '✅' if details['signal'] == 'BUY' else '❌' if details['signal'] == 'SELL' else '➖'
                message += f"\n{signal_icon} {indicator}: {details['reason']}"
    
    if include_recommendation:
        if analysis['signal'] in ['STRONG_BUY', 'BUY']:
            message += f"\n\n💡 Buy near ₹{analysis['current_price']}, Stop: ₹{analysis['stop_loss']}"
        elif analysis['signal'] in ['STRONG_SELL', 'SELL']:
            message += f"\n\n💡 Sell/Avoid, Stop: ₹{analysis['stop_loss']}"
        else:
            message += f"\n\n💡 Wait for clearer signals"
    
    return message

# MESSAGE FORMAT EXAMPLES:

def show_message_examples():
    """Show examples of different message formats"""
    
    # Sample analysis data
    sample_analysis = {
        'symbol': 'GBIME',
        'signal': 'BUY',
        'strength': 83.3,
        'current_price': 450.00,
        'target_price': 495.00,
        'stop_loss': 427.50,
        'risk_reward_ratio': 2.0,
        'support': 435.00,
        'resistance': 485.00,
        'buy_signals': 5,
        'sell_signals': 1,
        'neutral_signals': 0,
        'total_indicators': 6,
        'individual_signals': {
            'MACD': {'signal': 'BUY', 'reason': 'MACD bullish crossover'},
            'RSI': {'signal': 'BUY', 'reason': 'RSI rising above 50 (55.2)'},
            'MA_Trend': {'signal': 'BUY', 'reason': 'Price above MA20 above MA50'},
        }
    }
    
    print("📱 MESSAGE FORMAT EXAMPLES:")
    print("=" * 60)
    
    print("\n🔥 SHORT FORMAT:")
    print(format_short_message(sample_analysis))
    
    print("\n📊 MEDIUM FORMAT:")
    print(format_medium_message(sample_analysis))
    
    print("\n📋 DETAILED FORMAT:")
    print(format_detailed_message(sample_analysis)[:500] + "...")
    
    print("\n⚙️ CUSTOM FORMAT (minimal):")
    print(format_custom_message(sample_analysis, include_details=False, include_indicators=False, include_recommendation=True))

if __name__ == "__main__":
    show_message_examples() 