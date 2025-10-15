"""
Email Configuration
==================

This file contains the email configuration settings for the MACD Signal Giver.

SMTP Settings:
- Email: adwinlamal@gmail.com
- Password: vjbp zwtf smof dlun (App Password)
- Recipient: balaramlamsal137@gmail.com
- Server: smtp.gmail.com
- Port: 587
"""

# Email Configuration
SMTP_EMAIL = "adwinlamal@gmail.com"
SMTP_PASSWORD = "vjbp zwtf smof dlun"  # Gmail App Password
RECIPIENT_EMAIL = "balaramlamsal137@gmail.com"

# Optional: multiple recipients (To). The app will send to all listed here.
# Keep RECIPIENT_EMAIL for backward compatibility.
RECIPIENT_EMAILS = [
    "balaramlamsal137@gmail.com",
]

# SMTP Server Settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Email Templates
EMAIL_TEMPLATES = {
    "general_signal": {
        "subject_prefix": "📈 MACD Signal Alert",
        "body_template": """
        <h2>{signal_type}</h2>
        <p><strong>Stock:</strong> {stock_symbol}</p>
        <p><strong>RSI:</strong> {rsi:.1f} {rsi_emoji} {rsi_status}</p>
        <p><strong>Price:</strong> {price:.2f}</p>
        <p><strong>Date:</strong> {date}</p>
        <p><strong>MACD:</strong> {macd:.4f}</p>
        <p><strong>Signal Line:</strong> {signal:.4f}</p>
        <hr>
        <p><em>⚠️ Always do your own research before trading!</em></p>
        """
    },
    "portfolio_signal": {
        "subject_prefix": "🚨 Portfolio MACD Signal Alert",
        "body_template": """
        <h2>📊 Portfolio MACD Signal Alert</h2>
        <hr>
        <h3>{signal_emoji} {stock} - {signal_type}</h3>
        <p><strong>Date:</strong> {date}</p>
        <p><strong>MACD:</strong> {macd}</p>
        <p><strong>Signal Line:</strong> {signal}</p>
        <p>{action_message}</p>
        <hr>
        <p><em>⚠️ Always do your own research before trading!</em></p>
        """
    },
    "portfolio_rsi": {
        "subject_prefix": "📊 Portfolio RSI Status Report",
        "body_template": """
        <h2>📊 YOUR PORTFOLIO RSI STATUS</h2>
        <hr>
        {stock_details}
        <h3>📊 SUMMARY:</h3>
        <p>🟢 Oversold: {oversold_count}</p>
        <p>🔴 Overbought: {overbought_count}</p>
        <p>⚪ Neutral: {neutral_count}</p>
        <hr>
        <p><em>⚠️ Always do your own research before trading!</em></p>
        """
    },
    "ipo_alert": {
        "subject_prefix": "🎯 Open IPO Alert",
        "body_template": """
        <h2>🎯 Open IPO Alert!</h2>
        <hr>
        <h3>🏢 Company: {company_name}</h3>
        <p><strong>📈 Symbol:</strong> {symbol}</p>
        <p><strong>🏭 Sector:</strong> {sector}</p>
        <p><strong>💰 Price per Unit:</strong> Rs. {price}</p>
        <p><strong>📊 Min Units:</strong> {min_units}</p>
        <p><strong>📊 Max Units:</strong> {max_units}</p>
        <p><strong>💼 Total Amount:</strong> Rs. {total_amount}</p>
        <p><strong>📅 Opens:</strong> {opens}</p>
        <p><strong>📅 Closes:</strong> {closes}</p>
        <p><strong>🏛️ Registrar:</strong> {registrar}</p>
        {rating_line}
        <hr>
        <p><em>💡 Don't miss this investment opportunity!</em></p>
        """
    }
}

# Portfolio Stocks
PORTFOLIO_STOCKS = ['CFCL', 'PFL', 'ICFC', 'JFL', 'BFC','SIKLES',]

# RSI Thresholds
RSI_OVERSOLD_THRESHOLD = 30
RSI_OVERBOUGHT_THRESHOLD = 70
# Additional alert threshold for general stocks RSI low alerts
RSI_LOW_ALERT_THRESHOLD = 35

# MACD Settings
MACD_SHORT_WINDOW = 12
MACD_LONG_WINDOW = 26
MACD_SIGNAL_WINDOW = 9

# RSI Settings
RSI_PERIOD = 14

# Signal Detection Settings
RECENT_SIGNALS_DAYS = 5  # Number of days to look back for recent signals 