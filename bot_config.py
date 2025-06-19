# 🔧 Bot Configuration Settings

# MESSAGE FORMAT SETTINGS
# Choose your preferred message format:
# Options: 'short', 'medium', 'detailed'
MESSAGE_FORMAT = 'short'  # Change this to 'medium' or 'detailed' for longer messages

# SIGNAL THRESHOLD SETTINGS
# Minimum number of indicators needed for BUY/SELL signals
MIN_BUY_SIGNALS = 3    # Default: 3 (out of 6 indicators)
MIN_SELL_SIGNALS = 3   # Default: 3 (out of 6 indicators)

# RISK MANAGEMENT SETTINGS
DEFAULT_STOP_LOSS_PERCENT = 5    # Default: 5% stop loss
DEFAULT_TARGET_PERCENT = 10      # Default: 10% target
SUPPORT_RESISTANCE_BUFFER = 2    # Default: 2% buffer from S&R levels

# RSI SETTINGS
RSI_OVERSOLD_LEVEL = 30    # Default: 30 (buy when below this)
RSI_OVERBOUGHT_LEVEL = 70  # Default: 70 (sell when above this)

# MOVING AVERAGE SETTINGS
MA_SHORT_PERIOD = 20   # Default: 20-day MA
MA_LONG_PERIOD = 50    # Default: 50-day MA

# BOLLINGER BANDS SETTINGS
BB_PERIOD = 20         # Default: 20-day period
BB_STD_DEV = 2         # Default: 2 standard deviations

# TELEGRAM SETTINGS
SEND_ONLY_STRONG_SIGNALS = False  # Set to True to only send STRONG_BUY/STRONG_SELL
INCLUDE_PORTFOLIO_HEADER = True   # Add "YOUR PORTFOLIO ALERT" header for personal stocks

# QUICK PRESETS
PRESETS = {
    'conservative': {
        'MESSAGE_FORMAT': 'short',
        'MIN_BUY_SIGNALS': 4,
        'MIN_SELL_SIGNALS': 4,
        'SEND_ONLY_STRONG_SIGNALS': True
    },
    'balanced': {
        'MESSAGE_FORMAT': 'medium',
        'MIN_BUY_SIGNALS': 3,
        'MIN_SELL_SIGNALS': 3,
        'SEND_ONLY_STRONG_SIGNALS': False
    },
    'aggressive': {
        'MESSAGE_FORMAT': 'detailed',
        'MIN_BUY_SIGNALS': 2,
        'MIN_SELL_SIGNALS': 2,
        'SEND_ONLY_STRONG_SIGNALS': False
    }
}

# To use a preset, uncomment one of these:
# ACTIVE_PRESET = 'conservative'  # Only strong signals, short messages
# ACTIVE_PRESET = 'balanced'      # Medium signals, medium messages
# ACTIVE_PRESET = 'aggressive'    # More signals, detailed messages

def get_message_formatter():
    """Get the appropriate message formatter based on config"""
    from message_formats import format_short_message, format_medium_message, format_detailed_message
    
    formatters = {
        'short': format_short_message,
        'medium': format_medium_message,
        'detailed': format_detailed_message
    }
    
    return formatters.get(MESSAGE_FORMAT, format_short_message)

def apply_preset(preset_name):
    """Apply a configuration preset"""
    if preset_name in PRESETS:
        preset = PRESETS[preset_name]
        globals().update(preset)
        print(f"✅ Applied {preset_name} preset")
        print(f"   Message Format: {MESSAGE_FORMAT}")
        print(f"   Min Buy Signals: {MIN_BUY_SIGNALS}")
        print(f"   Strong Signals Only: {SEND_ONLY_STRONG_SIGNALS}")
    else:
        print(f"❌ Preset '{preset_name}' not found")

# Apply preset if one is set
if 'ACTIVE_PRESET' in locals():
    apply_preset(ACTIVE_PRESET) 