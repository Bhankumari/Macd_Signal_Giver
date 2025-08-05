# MACD Signal Email Notifier

This application fetches stock data, calculates MACD indicators, and sends buy/sell signals via email notifications.

## Features

- **MACD Signal Detection**: Analyzes stock data for MACD crossover signals
- **RSI Analysis**: Monitors RSI levels for oversold/overbought conditions
- **Portfolio Tracking**: Tracks specific stocks in your portfolio
- **IPO Alerts**: Notifies about open IPO opportunities
- **Email Notifications**: Sends detailed alerts via email instead of Telegram

## Email Configuration

The application uses Gmail SMTP to send email notifications. Configure your email settings in `email_config.py`:

```python
# Email Configuration
SMTP_EMAIL = "adwinlamal@gmail.com"
SMTP_PASSWORD = "vjbp zwtf smof dlun"  # Gmail App Password
RECIPIENT_EMAIL = "balaramlamsal137@gmail.com"
```

### Setting up Gmail App Password

1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account Settings > Security > App Passwords
3. Generate an app password for "Mail"
4. Use this password in the configuration (not your regular Gmail password)

## Portfolio Configuration

Update your portfolio stocks in `email_config.py`:

```python
PORTFOLIO_STOCKS = ['CFCL', 'JFL', 'PFL', 'ICFC', 'JFL', 'BFC']
```

## Local Development

To run the application locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Test email functionality
python test_email.py

# Run the main analysis
python main.py
```

## Email Notifications

The application sends different types of email notifications:

1. **General Stock Signals**: MACD crossover signals for all tracked stocks
2. **Portfolio Alerts**: MACD signals specifically for your portfolio stocks
3. **RSI Status Reports**: Daily RSI analysis for portfolio stocks
4. **IPO Alerts**: Notifications about open IPO opportunities

## Configuration Files

- `email_config.py`: Email settings and templates
- `stock_list.csv`: List of stocks to analyze
- `my_portfolio.csv`: Your portfolio holdings
- `data/`: Directory containing stock price data

## Testing

Before running the main application, test the email functionality:

```bash
python test_email.py
```

This will send a test email to verify that your SMTP configuration is working correctly.

## Data Sources

- **Stock Data**: Fetched from sharesansar.com
- **IPO Data**: Fetched from nepalipaisa.com
- **Price History**: Stored locally in CSV files

## Signal Types

- **Buy Signal**: MACD line crosses above signal line (bullish)
- **Sell Signal**: MACD line crosses below signal line (bearish)
- **RSI Oversold**: RSI < 30 (potential buy opportunity)
- **RSI Overbought**: RSI > 70 (potential sell opportunity)

## Disclaimer

⚠️ **Always do your own research before trading!** This application provides technical analysis signals but should not be used as the sole basis for investment decisions. 