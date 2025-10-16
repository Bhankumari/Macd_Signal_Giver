import requests
import json
import csv
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import asyncio
import aiohttp
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any
from email_config import (
    SMTP_EMAIL, SMTP_PASSWORD, RECIPIENT_EMAIL, SMTP_SERVER, SMTP_PORT,
    PORTFOLIO_STOCKS, EMAIL_TEMPLATES, RSI_OVERSOLD_THRESHOLD, RSI_OVERBOUGHT_THRESHOLD,
    RECIPIENT_EMAILS, RSI_LOW_ALERT_THRESHOLD
)

class EmailSender:
    def __init__(self, smtp_email=None, smtp_password=None, recipient_email=None, recipient_emails=None):
        self.smtp_email = smtp_email or SMTP_EMAIL
        self.smtp_password = smtp_password or SMTP_PASSWORD
        # Backward-compatible single recipient
        single_recipient = recipient_email or RECIPIENT_EMAIL
        # Preferred multiple recipients list
        configured_recipients = RECIPIENT_EMAILS if isinstance(RECIPIENT_EMAILS, list) else []
        # Allow override via arg
        if recipient_emails is not None:
            configured_recipients = recipient_emails if isinstance(recipient_emails, list) else [recipient_emails]
        # Fallback to single if list empty
        self.recipient_emails = configured_recipients or ([single_recipient] if single_recipient else [])
        # Expose first recipient for existing prints/tests
        self.recipient_email = self.recipient_emails[0] if self.recipient_emails else ""
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
    
    def send_email(self, subject, message):
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_email
            msg['To'] = ", ".join(self.recipient_emails) if self.recipient_emails else self.recipient_email
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(message, 'html'))
            
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_email, self.smtp_password)
            
            # Send email
            text = msg.as_string()
            to_addresses = self.recipient_emails if self.recipient_emails else [self.recipient_email]
            server.sendmail(self.smtp_email, to_addresses, text)
            server.quit()
            
            print(f"📧 Email sent successfully to {', '.join(to_addresses)}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False

class PortfolioMACDAnalyzer:
    def __init__(self, email_sender=None):
        self.my_stocks = PORTFOLIO_STOCKS
        self.portfolio_data = []
        self.macd_signals = {}
        self.rsi_alerts = {}
        self.email_sender = email_sender
        
    def load_portfolio_from_csv(self, filename='my_portfolio.csv'):
        """Load portfolio data from CSV file"""
        try:
            df = pd.read_csv(filename)
            return df
        except FileNotFoundError:
            print(f"Portfolio file {filename} not found!")
            return None
    
    async def analyze_portfolio_macd_signals(self):
        """Analyze MACD signals for all stocks in portfolio"""
        signal_date = datetime.today().strftime('%Y-%m-%d')
        
        print(f"\n🔍 Analyzing Portfolio MACD signals for {signal_date}...")
        print("=" * 60)
        
        portfolio_signals_found = []
        
        for stock_symbol in self.my_stocks:
            try:
                file_path = f"data/{stock_symbol}.csv"
                
                if not os.path.exists(file_path):
                    print(f"⚠️  No data file found for {stock_symbol}")
                    self.macd_signals[stock_symbol] = "No Data"
                    continue
                
                # Load and process data
                data = pd.read_csv(file_path)
                data.columns = [col.lower() for col in data.columns]
                data = data[['published_date', 'close']]
                data['published_date'] = pd.to_datetime(data['published_date'])
                data['close'] = pd.to_numeric(data['close'], errors='coerce')
                data = data.dropna(subset=['close'])
                data = data.sort_values(by='published_date')
                
                if len(data) < 26:  # Need at least 26 data points for MACD
                    print(f"⚠️  Insufficient data for {stock_symbol} (need 26+ points, have {len(data)})")
                    self.macd_signals[stock_symbol] = "Insufficient Data"
                    continue
                
                # Calculate MACD
                macd_data = calculate_macd(data)
                
                # Check for recent crossovers (last 5 days)
                recent_signals = self.detect_recent_crossovers(macd_data, stock_symbol)
                self.macd_signals[stock_symbol] = recent_signals
                
                # If signals found, add to portfolio signals list
                if isinstance(recent_signals, list) and len(recent_signals) > 0:
                    for signal in recent_signals:
                        portfolio_signals_found.append({
                            'stock': stock_symbol,
                            'signal': signal
                        })
                
            except Exception as e:
                print(f"❌ Error analyzing {stock_symbol}: {str(e)}")
                self.macd_signals[stock_symbol] = "Error"
        
        # Send email messages for portfolio signals
        if portfolio_signals_found and self.email_sender:
            await self.send_portfolio_email_messages(portfolio_signals_found)
    
    async def send_portfolio_email_messages(self, portfolio_signals):
        """Send email messages for portfolio stocks with MACD signals"""
        if not portfolio_signals:
            return
            
        subject = "🚨 Portfolio MACD Signal Alert"
        message_lines = ["<h2>📊 Portfolio MACD Signal Alert</h2>", "<hr>"]
        
        for signal_info in portfolio_signals:
            stock = signal_info['stock']
            signal = signal_info['signal']
            signal_type = signal['type']
            date = signal['date'].strftime('%Y-%m-%d')
            
            # Create message for user's portfolio stocks
            if signal_type == 'BUY':
                message_lines.append(f"<h3>🟢 {stock} - BUY SIGNAL</h3>")
                message_lines.append(f"<p><strong>Date:</strong> {date}</p>")
                message_lines.append(f"<p><strong>MACD:</strong> {signal['macd']}</p>")
                message_lines.append(f"<p><strong>Signal Line:</strong> {signal['signal']}</p>")
                message_lines.append("<p>📈 Consider reviewing your position!</p>")
            else:
                message_lines.append(f"<h3>🔴 {stock} - SELL SIGNAL</h3>")
                message_lines.append(f"<p><strong>Date:</strong> {date}</p>")
                message_lines.append(f"<p><strong>MACD:</strong> {signal['macd']}</p>")
                message_lines.append(f"<p><strong>Signal Line:</strong> {signal['signal']}</p>")
                message_lines.append("<p>📉 Consider reviewing your position!</p>")
            
            message_lines.append("<hr>")
        
        message_lines.append("<p><em>⚠️ Always do your own research before trading!</em></p>")
        
        message = "\n".join(message_lines)
        
        print(f"📧 Sending portfolio alert email...")
        self.email_sender.send_email(subject, message)

    def detect_recent_crossovers(self, data, stock_symbol, days_back=5):
        """Detect MACD crossovers in recent days"""
        signals = []
        
        # Get recent data (last 'days_back' days)
        recent_data = data.tail(days_back)
        
        for i in range(1, len(recent_data)):
            current_idx = recent_data.index[i]
            prev_idx = recent_data.index[i-1]
            
            macd_current = recent_data.loc[current_idx, 'macd']
            signal_current = recent_data.loc[current_idx, 'signal']
            macd_prev = recent_data.loc[prev_idx, 'macd']
            signal_prev = recent_data.loc[prev_idx, 'signal']
            date_current = recent_data.loc[current_idx, 'published_date']
            
            # Check for crossovers
            if (macd_current > signal_current and macd_prev <= signal_prev):
                signals.append({
                    'type': 'BUY',
                    'date': date_current,
                    'macd': round(macd_current, 4),
                    'signal': round(signal_current, 4)
                })
            elif (macd_current < signal_current and macd_prev >= signal_prev):
                signals.append({
                    'type': 'SELL',
                    'date': date_current,
                    'macd': round(macd_current, 4),
                    'signal': round(signal_current, 4)
                })
        
        return signals if signals else "No Recent Signals"
    
    def display_portfolio_analysis(self):
        """Display portfolio analysis with MACD highlights"""
        print("\n" + "="*80)
        print("📊 PORTFOLIO MACD ANALYSIS REPORT")
        print("="*80)
        
        # Load portfolio data
        portfolio_df = self.load_portfolio_from_csv()
        
        if portfolio_df is None:
            print("❌ Could not load portfolio data!")
            return
        
        highlighted_stocks = []
        
        for index, row in portfolio_df.iterrows():
            stock = row['Symbol']
            balance = row['Current_Balance'] if pd.notna(row['Current_Balance']) else 0
            ltp = row['Last_Transaction_Price'] if pd.notna(row['Last_Transaction_Price']) else 0
            value_ltp = row['Value_LTP'] if pd.notna(row['Value_LTP']) else 0
            
            print(f"\n📈 {stock}")
            print(f"   Balance: {balance} | LTP: {ltp} | Value: {value_ltp}")
            
            # Check RSI status
            if stock in self.rsi_alerts:
                rsi_info = self.rsi_alerts[stock]
                if isinstance(rsi_info, dict):
                    rsi_value = rsi_info['rsi']
                    rsi_status = rsi_info['status']
                    
                    if rsi_status == 'OVERSOLD':
                        print(f"   🟢 RSI: {rsi_value:.1f} - OVERSOLD (Buy opportunity)")
                    elif rsi_status == 'OVERBOUGHT':
                        print(f"   🔴 RSI: {rsi_value:.1f} - OVERBOUGHT (Consider selling)")
                    else:
                        print(f"   ⚪ RSI: {rsi_value:.1f} - NEUTRAL")
                else:
                    print(f"   ⚠️  RSI: {rsi_info}")
            
            # Check MACD signals
            if stock in self.macd_signals:
                signals = self.macd_signals[stock]
                
                if isinstance(signals, list) and len(signals) > 0:
                    print("   🚨 MACD SIGNALS DETECTED:")
                    highlighted_stocks.append(stock)
                    
                    for signal in signals:
                        signal_type = signal['type']
                        date = signal['date'].strftime('%Y-%m-%d')
                        
                        if signal_type == 'BUY':
                            print(f"   🟢 BUY SIGNAL on {date}")
                        else:
                            print(f"   🔴 SELL SIGNAL on {date}")
                        
                        print(f"      MACD: {signal['macd']} | Signal Line: {signal['signal']}")
                    
                elif signals == "No Recent Signals":
                    print("   ⚪ No recent MACD signals")
                else:
                    print(f"   ⚠️  {signals}")
            else:
                print("   ❓ MACD analysis not available")
        
        # Summary
        print("\n" + "="*80)
        print("📋 SUMMARY")
        print("="*80)
        
        if highlighted_stocks:
            print(f"🚨 STOCKS WITH MACD SIGNALS: {', '.join(highlighted_stocks)}")
            print("   👆 These stocks have recent MACD crossovers - consider reviewing!")
        else:
            print("✅ No recent MACD crossover signals detected in your portfolio")
        
        print(f"📊 Total stocks analyzed: {len(self.my_stocks)}")
        print(f"💼 Portfolio symbols: {', '.join(self.my_stocks)}")
    
    def update_csv_with_signals(self):
        """Update the portfolio CSV with MACD signal status"""
        try:
            df = pd.read_csv('my_portfolio.csv')
            
            for index, row in df.iterrows():
                stock = row['Symbol']
                if stock in self.macd_signals:
                    signals = self.macd_signals[stock]
                    
                    if isinstance(signals, list) and len(signals) > 0:
                        # Get the most recent signal
                        latest_signal = signals[-1]
                        status = f"{latest_signal['type']} Signal ({latest_signal['date'].strftime('%m/%d')})"
                        df.at[index, 'MACD_Status'] = status
                    elif signals == "No Recent Signals":
                        df.at[index, 'MACD_Status'] = "No Signals"
                    else:
                        df.at[index, 'MACD_Status'] = str(signals)
            
            df.to_csv('my_portfolio.csv', index=False)
            print("\n✅ Portfolio CSV updated with MACD signals!")
            
        except Exception as e:
            print(f"❌ Error updating CSV: {str(e)}")

    def calculate_rsi(self, data, period=14):
        """
        Calculate RSI using Wilder's smoothing method (the correct/standard way)
        This matches what you see on TradingView, Yahoo Finance, etc.
        """
        close_prices = data['close'].copy()
        
        # Calculate price changes
        delta = close_prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate the first averages using simple moving average
        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()
        
        # Apply Wilder's smoothing for subsequent values
        for i in range(period, len(gains)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gains.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + losses.iloc[i]) / period
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    async def check_personal_stocks_rsi(self):
        """Check RSI levels for personal stocks and alert if oversold/overbought"""
        print(f"\n📊 Checking RSI levels for personal stocks...")
        print("=" * 60)
        
        rsi_alerts = []
        
        for stock_symbol in self.my_stocks:
            try:
                file_path = f"data/{stock_symbol}.csv"
                
                if not os.path.exists(file_path):
                    print(f"⚠️  No data file found for {stock_symbol}")
                    continue
                
                # Load and process data
                data = pd.read_csv(file_path)
                data.columns = [col.lower() for col in data.columns]
                data = data[['published_date', 'close']]
                data['published_date'] = pd.to_datetime(data['published_date'])
                data['close'] = pd.to_numeric(data['close'], errors='coerce')
                data = data.dropna(subset=['close'])
                data = data.sort_values(by='published_date')
                
                if len(data) < 14:  # Need at least 14 data points for RSI
                    print(f"⚠️  Insufficient data for {stock_symbol} RSI (need 14+ points, have {len(data)})")
                    continue
                
                # Calculate RSI
                rsi = self.calculate_rsi(data)
                current_rsi = rsi.iloc[-1]
                current_price = data['close'].iloc[-1]
                
                # Check for oversold or overbought conditions
                rsi_status = None
                alert_emoji = ""
                
                if current_rsi < RSI_OVERSOLD_THRESHOLD:
                    rsi_status = "OVERSOLD"
                    alert_emoji = "🟢"  # Green for potential buy opportunity
                elif current_rsi > RSI_OVERBOUGHT_THRESHOLD:
                    rsi_status = "OVERBOUGHT"
                    alert_emoji = "🔴"  # Red for potential sell opportunity
                
                # Always show RSI value for personal stocks
                print(f"📈 {stock_symbol}: RSI = {current_rsi:.1f} | Price = {current_price:.2f}", end="")
                
                if rsi_status:
                    print(f" {alert_emoji} {rsi_status}")
                    rsi_alerts.append({
                        'stock': stock_symbol,
                        'rsi': current_rsi,
                        'price': current_price,
                        'status': rsi_status,
                        'emoji': alert_emoji
                    })
                else:
                    print(" ⚪ NEUTRAL")
                
                self.rsi_alerts[stock_symbol] = {
                    'rsi': current_rsi,
                    'price': current_price,
                    'status': rsi_status or 'NEUTRAL'
                }
                
            except Exception as e:
                print(f"❌ Error checking RSI for {stock_symbol}: {str(e)}")
                self.rsi_alerts[stock_symbol] = "Error"
        
        # Do not send RSI status for portfolio via email
    
    async def send_portfolio_rsi_status(self):
        """Always send RSI status for ALL portfolio stocks via email"""
        if not self.rsi_alerts:
            return
        
        # Create comprehensive RSI status message for all stocks
        subject = "📊 Portfolio RSI Status Report"
        message_lines = ["<h2>📊 YOUR PORTFOLIO RSI STATUS</h2>", "<hr>"]
        
        oversold_count = 0
        overbought_count = 0
        neutral_count = 0
        
        for stock_symbol in self.my_stocks:
            if stock_symbol in self.rsi_alerts and isinstance(self.rsi_alerts[stock_symbol], dict):
                rsi_info = self.rsi_alerts[stock_symbol]
                rsi = rsi_info['rsi']
                price = rsi_info['price']
                status = rsi_info['status']
                
                if status == 'OVERSOLD':
                    emoji = "🟢"
                    oversold_count += 1
                    message_lines.append(f"<h3>{emoji} {stock_symbol}: RSI {rsi:.1f} - {status}</h3>")
                    message_lines.append(f"<p><strong>Price:</strong> {price:.2f}</p>")
                    message_lines.append("<p>💡 Potential BUY opportunity</p>")
                elif status == 'OVERBOUGHT':
                    emoji = "🔴"
                    overbought_count += 1
                    message_lines.append(f"<h3>{emoji} {stock_symbol}: RSI {rsi:.1f} - {status}</h3>")
                    message_lines.append(f"<p><strong>Price:</strong> {price:.2f}</p>")
                    message_lines.append("<p>💡 Consider taking profits</p>")
                else:
                    emoji = "⚪"
                    neutral_count += 1
                    message_lines.append(f"<h3>{emoji} {stock_symbol}: RSI {rsi:.1f} - {status}</h3>")
                    message_lines.append(f"<p><strong>Price:</strong> {price:.2f}</p>")
                
                message_lines.append("<hr>")
        
        # Add summary
        message_lines.append("<h3>📊 SUMMARY:</h3>")
        message_lines.append(f"<p>🟢 Oversold: {oversold_count}</p>")
        message_lines.append(f"<p>🔴 Overbought: {overbought_count}</p>")
        message_lines.append(f"<p>⚪ Neutral: {neutral_count}</p>")
        message_lines.append("<hr>")
        message_lines.append("<p><em>⚠️ Always do your own research before trading!</em></p>")
        
        message = "\n".join(message_lines)
        
        print(f"📧 Sending complete portfolio RSI status via email...")
        self.email_sender.send_email(subject, message)

class IPOChecker:
    def __init__(self, email_sender=None):
        self.email_sender = email_sender
    
    def fetch_ipo_data(self) -> Dict[str, Any]:
        """
        Fetch IPO data from Nepali Paisa API
        Returns the JSON response from the API
        """
        url = "https://nepalipaisa.com/api/GetIpos"
        
        # Parameters from the curl command
        params = {
            'stockSymbol': '',
            'pageNo': 1,
            'itemsPerPage': 10,
            'pagePerDisplay': 5,
            '_': int(datetime.now().timestamp() * 1000)  # current timestamp
        }
        
        # Headers from the curl command
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9,ne;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json; charset=utf-8',
            'Referer': 'https://nepalipaisa.com/ipo',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching IPO data: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return {}

    def is_ipo_open(self, ipo: Dict[str, Any]) -> bool:
        """
        Check if an IPO is currently open for application
        This function checks various status fields to determine if IPO is open
        """
        # Check the status field directly
        if 'status' in ipo:
            status = str(ipo['status']).lower()
            if 'open' in status:
                return True
            elif any(keyword in status for keyword in ['closed', 'end', 'completed', 'finished']):
                return False
        
        # Check date-based opening/closing using the actual API field names
        current_date = datetime.now()
        
        open_date = None
        close_date = None
        
        # Parse opening date
        if 'openingDateAD' in ipo and ipo['openingDateAD']:
            try:
                open_date = datetime.strptime(ipo['openingDateAD'], '%Y-%m-%d')
            except (ValueError, TypeError):
                pass
        
        # Parse closing date
        if 'closingDateAD' in ipo and ipo['closingDateAD']:
            try:
                close_date = datetime.strptime(ipo['closingDateAD'], '%Y-%m-%d')
            except (ValueError, TypeError):
                pass
        
        # If we have both dates, check if current date is between them
        if open_date and close_date:
            return open_date <= current_date <= close_date
        
        # If no clear indicators, return False (better to be conservative)
        return False

    def format_ipo_for_email(self, ipo: Dict[str, Any]) -> str:
        """
        Format IPO details for email message
        """
        message_lines = ["<h2>🎯 Open IPO Alert!</h2>", "<hr>"]
        message_lines.append(f"<h3>🏢 Company: {ipo.get('companyName', 'Unknown Company')}</h3>")
        message_lines.append(f"<p><strong>📈 Symbol:</strong> {ipo.get('stockSymbol', 'N/A')}</p>")
        message_lines.append(f"<p><strong>🏭 Sector:</strong> {ipo.get('sectorName', 'N/A')}</p>")
        message_lines.append(f"<p><strong>💰 Price per Unit:</strong> Rs. {ipo.get('pricePerUnit', 'N/A')}</p>")
        message_lines.append(f"<p><strong>📊 Min Units:</strong> {ipo.get('minUnits', 'N/A')}</p>")
        message_lines.append(f"<p><strong>📊 Max Units:</strong> {ipo.get('maxUnits', 'N/A')}</p>")
        message_lines.append(f"<p><strong>💼 Total Amount:</strong> Rs. {ipo.get('totalAmount', 'N/A')}</p>")
        message_lines.append(f"<p><strong>📅 Opens:</strong> {ipo.get('openingDateAD', 'N/A')}</p>")
        message_lines.append(f"<p><strong>📅 Closes:</strong> {ipo.get('closingDateAD', 'N/A')}</p>")
        message_lines.append(f"<p><strong>🏛️ Registrar:</strong> {ipo.get('shareRegistrar', 'N/A')}</p>")
        if ipo.get('rating'):
            message_lines.append(f"<p><strong>⭐ Rating:</strong> {ipo.get('rating')}</p>")
        message_lines.append("<hr>")
        message_lines.append("<p><em>💡 Don't miss this investment opportunity!</em></p>")
        
        return "\n".join(message_lines)

    async def check_and_notify_ipos(self):
        """
        Check for open IPOs and send email notifications
        """
        print("\n🔍 Checking for open IPOs...")
        print("=" * 60)
        
        data = self.fetch_ipo_data()
        
        if not data:
            print("❌ Failed to fetch IPO data or received empty response.")
            return
        
        # Parse IPO data from API response
        ipos = []
        if isinstance(data, dict):
            if 'result' in data and isinstance(data['result'], dict) and 'data' in data['result']:
                ipos = data['result']['data'] if isinstance(data['result']['data'], list) else []
            elif 'data' in data:
                ipos = data['data'] if isinstance(data['data'], list) else [data['data']]
            elif 'ipos' in data:
                ipos = data['ipos'] if isinstance(data['ipos'], list) else [data['ipos']]
            else:
                ipos = [data]
        elif isinstance(data, list):
            ipos = data
        
        if not ipos:
            print("❌ No IPO data found in the response.")
            return
        
        # Filter for open IPOs
        open_ipos = [ipo for ipo in ipos if self.is_ipo_open(ipo)]
        
        if open_ipos:
            print(f"🎯 Found {len(open_ipos)} open IPO(s)!")
            
            # Send email notifications for each open IPO
            if self.email_sender:
                for ipo in open_ipos:
                    subject = f"🎯 Open IPO Alert: {ipo.get('companyName', 'Unknown')}"
                    message = self.format_ipo_for_email(ipo)
                    print(f"📧 Sending IPO alert for {ipo.get('companyName', 'Unknown')}...")
                    self.email_sender.send_email(subject, message)
            
            # Display details in console
            for i, ipo in enumerate(open_ipos, 1):
                print(f"\n📋 Open IPO #{i}:")
                print(f"   Company: {ipo.get('companyName', 'Unknown')}")
                print(f"   Symbol: {ipo.get('stockSymbol', 'N/A')}")
                print(f"   Price: Rs. {ipo.get('pricePerUnit', 'N/A')}")
                print(f"   Closes: {ipo.get('closingDateAD', 'N/A')}")
                
        else:
            print("✅ No open IPOs found at the moment.")
            print(f"📊 Total IPOs checked: {len(ipos)}")
            
            # Show recent IPOs for reference
            if ipos:
                print("\n📋 Recent IPOs:")
                for i, ipo in enumerate(ipos[:3], 1):
                    print(f"   {i}. {ipo.get('companyName', 'Unknown')} ({ipo.get('stockSymbol', 'N/A')}): {ipo.get('status', 'Status unknown')}")

def fetch_cookies_and_csrf_token(url, headers):
    """Fetch cookies and CSRF token from the given URL."""
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    cookies = response.cookies.get_dict()
    soup = BeautifulSoup(response.text, "html.parser")
    save_json_from_response(soup, "company_data.json")

    csrf_token = soup.find("meta", {"name": "_token"})
    return cookies, csrf_token["content"] if csrf_token else None

def save_json_from_response(soup, filename):
    """Extract JSON data from the page's script tags and save it to a file."""
    script_tags = soup.find_all("script")
    json_data = None

    for script_tag in script_tags:
        if script_tag.string and "cmpjson" in script_tag.string:
            script_content = script_tag.string.strip()
            start = script_content.find("[")
            end = script_content.rfind("]") + 1
            json_data = script_content[start:end]
            break

    if json_data:
        try:
            data = json.loads(json_data)
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print(f"JSON data saved to {filename}")
        except json.JSONDecodeError:
            print("Failed to decode JSON from the script content.")
    else:
        print("No suitable <script> tag with JSON data found.")

def update_headers(headers, cookies, csrf_token):
    """Update headers with cookies and CSRF token."""
    if cookies:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token
    return headers

def price_history(headers, company_id):
    """Fetch price history for a specific company."""
    payload = {
        "draw": 1,
        "start": 0,
        "length": 50,
        "search[value]": "",
        "search[regex]": "false",
        "company": company_id
    }

    url = "https://www.sharesansar.com/company-price-history"
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        data = json.loads(response.text).get('data', [])
        return data
    else:
        print(f"Failed to fetch data: {response.status_code}")
        print(response.text)
        return []

def update_csv(company_symbol, new_data):
    """Update the CSV file with new data, avoiding duplicates."""
    file_path = f"data/{company_symbol}.csv"

    try:
        # Load existing data
        old_data = pd.read_csv(file_path)
    except FileNotFoundError:
        # Create a new file if it doesn't exist
        old_data = pd.DataFrame()

    new_data_df = pd.DataFrame(new_data)

    if not old_data.empty:
        # Ensure data types match
        old_data['published_date'] = pd.to_datetime(old_data['published_date'])
        new_data_df['published_date'] = pd.to_datetime(new_data_df['published_date'])

        # Filter out duplicates
        new_data_filtered = new_data_df[~new_data_df['published_date'].isin(old_data['published_date'])]
    else:
        new_data_filtered = new_data_df

    # Exclude empty DataFrames before concatenation
    frames_to_concat = [df for df in [old_data, new_data_filtered] if not df.empty]
    combined_data = pd.concat(frames_to_concat, ignore_index=True) if frames_to_concat else pd.DataFrame()

    # Sort by date and save
    combined_data.sort_values(by='published_date',ascending=False, inplace=True)
    combined_data.to_csv(file_path, index=False)

    print(f"Updated {company_symbol}.csv with {len(new_data_filtered)} new entries.")


def load_company_data(json_file, stock_list):
    """Load and filter company data based on stock list."""
    with open(json_file, "r", encoding="utf-8") as file:
        company_data = json.load(file)

    return [company for company in company_data if company["symbol"] in stock_list]


def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    """Function to calculate MACD and Signal line"""
    # Calculate short-term and long-term EMAs
    data['ema_short'] = data['close'].ewm(span=short_window, adjust=False).mean()
    data['ema_long'] = data['close'].ewm(span=long_window, adjust=False).mean()

    # Calculate MACD line
    data['macd'] = data['ema_short'] - data['ema_long']

    # Calculate Signal line
    data['signal'] = data['macd'].ewm(span=signal_window, adjust=False).mean()

    return data

def calculate_rsi_for_general_stocks(data, period=14):
    """
    Calculate RSI using Wilder's smoothing method for general stocks
    This matches the RSI calculation used for portfolio stocks
    """
    close_prices = data['close'].copy()
    
    # Calculate price changes
    delta = close_prices.diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calculate the first averages using simple moving average
    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()
    
    # Apply Wilder's smoothing for subsequent values
    for i in range(period, len(gains)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gains.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + losses.iloc[i]) / period
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def get_rsi_status_emoji(rsi_value):
    """Get RSI status and emoji based on RSI value"""
    if rsi_value < RSI_OVERSOLD_THRESHOLD:
        return "OVERSOLD", "🟢"
    elif rsi_value > RSI_OVERBOUGHT_THRESHOLD:
        return "OVERBOUGHT", "🔴"
    else:
        return "NEUTRAL", "⚪"


async def detect_intersections(data, company_symbol, signal_date, email_sender):
    """Function to detect MACD crossovers and print signals with RSI information"""
    intersections = []
    signals_found = []
    
    # Calculate RSI for this stock
    rsi_data = calculate_rsi_for_general_stocks(data)

    for i in range(1, len(data)):
        # Check for MACD crossing Signal line (Intersection)
        if (data['macd'].iloc[i] > data['signal'].iloc[i] and data['macd'].iloc[i - 1] <= data['signal'].iloc[i - 1]):
            # Buy signal: MACD crosses signal line from below
            intersections.append((data['published_date'].iloc[i], data['macd'].iloc[i], data['signal'].iloc[i], "Buy Signal", i))
        elif (data['macd'].iloc[i] < data['signal'].iloc[i] and data['macd'].iloc[i - 1] >= data['signal'].iloc[i - 1]):
            # Sell signal: MACD crosses signal line from above
            intersections.append((data['published_date'].iloc[i], data['macd'].iloc[i], data['signal'].iloc[i], "Sell Signal", i))

    # Print intersection points and signal types (symbol and price only)
    for date, macd_val, signal_val, signal_type, index in intersections:
        # Define today's date in the same format as the 'date' variable
        today_date = datetime.strptime(f"{signal_date} 00:00:00", "%Y-%m-%d %H:%M:%S")

        # Convert 'date' to datetime for consistent comparison
        intersection_date = datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")

        if intersection_date == today_date:
            # Get current price for this signal
            current_price = data['close'].iloc[index]

            # Print only signal type, symbol, and price
            print(f"\n\n{signal_type}: {company_symbol} | Price: {current_price:.2f} ({intersection_date.strftime('%Y-%m-%d')})")
        
            # Collect signal for batch email
            signals_found.append({
                'signal_type': signal_type,
                'stock_symbol': company_symbol,
                'price': current_price,
                'date': intersection_date.strftime('%Y-%m-%d'),
                'macd': macd_val,
                'signal': signal_val
            })

    return intersections, signals_found


async def send_summary_email(all_signals, email_sender, signal_date, ipo_alerts=None, low_rsi_alerts=None):
    """Send a summary email listing only MACD signals (symbol and price)."""
    has_signals = all_signals and len(all_signals) > 0
    has_ipos = False
    has_low_rsi = False
    
    if not has_signals:
        return
    
    # Count signals by type
    buy_signals = [s for s in all_signals if s['signal_type'] == 'Buy Signal']
    sell_signals = [s for s in all_signals if s['signal_type'] == 'Sell Signal']
    
    subject = f"📊 MACD Crossover Summary - {signal_date}"
    
    # Create summary message
    message_lines = [
        f"<h1>📊 MACD Crossover Report</h1>",
        f"<p><strong>Date:</strong> {signal_date}</p>",
        "<hr>"
    ]
    
    if has_signals:
        message_lines.extend([
            f"<h2>📈 MACD Signals</h2>",
            f"<p><strong>Total Signals Found:</strong> {len(all_signals)}</p>",
            f"<p><strong>Buy Signals:</strong> {len(buy_signals)}</p>",
            f"<p><strong>Sell Signals:</strong> {len(sell_signals)}</p>",
            "<hr>"
        ])
        
        if buy_signals:
            message_lines.append("<h3>🟢 Buy Signals</h3>")
            for signal in buy_signals:
                message_lines.append(f"<h4>📈 {signal['stock_symbol']}</h4>")
                message_lines.append(f"<p><strong>Price:</strong> {signal['price']:.2f}</p>")
                message_lines.append("<hr>")
        
        if sell_signals:
            message_lines.append("<h3>🔴 Sell Signals</h3>")
            for signal in sell_signals:
                message_lines.append(f"<h4>📉 {signal['stock_symbol']}</h4>")
                message_lines.append(f"<p><strong>Price:</strong> {signal['price']:.2f}</p>")
                message_lines.append("<hr>")
    
    if has_low_rsi:
        message_lines.extend([
            f"<h2>🟢 RSI Opportunities (RSI < {RSI_LOW_ALERT_THRESHOLD})</h2>",
            f"<p><strong>Stocks:</strong> {len(low_rsi_alerts)}</p>",
            "<hr>"
        ])
        for item in low_rsi_alerts:
            message_lines.append(f"<h3>🟢 {item['stock_symbol']}: RSI {item['rsi']:.1f}</h3>")
            message_lines.append(f"<p><strong>Price:</strong> {item['price']:.2f}</p>")
            message_lines.append("<hr>")

    if has_ipos:
        message_lines.extend([
            f"<h2>🎯 IPO Opportunities</h2>",
            f"<p><strong>Open IPOs Found:</strong> {len(ipo_alerts)}</p>",
            "<hr>"
        ])
        
        for ipo in ipo_alerts:
            message_lines.append(f"<h3>🏢 {ipo.get('companyName', 'Unknown Company')}</h3>")
            message_lines.append(f"<p><strong>📈 Symbol:</strong> {ipo.get('stockSymbol', 'N/A')}</p>")
            message_lines.append(f"<p><strong>🏭 Sector:</strong> {ipo.get('sectorName', 'N/A')}</p>")
            message_lines.append(f"<p><strong>💰 Price per Unit:</strong> Rs. {ipo.get('pricePerUnit', 'N/A')}</p>")
            message_lines.append(f"<p><strong>📊 Min Units:</strong> {ipo.get('minUnits', 'N/A')}</p>")
            message_lines.append(f"<p><strong>📊 Max Units:</strong> {ipo.get('maxUnits', 'N/A')}</p>")
            message_lines.append(f"<p><strong>💼 Total Amount:</strong> Rs. {ipo.get('totalAmount', 'N/A')}</p>")
            message_lines.append(f"<p><strong>📅 Opens:</strong> {ipo.get('openingDateAD', 'N/A')}</p>")
            message_lines.append(f"<p><strong>📅 Closes:</strong> {ipo.get('closingDateAD', 'N/A')}</p>")
            message_lines.append(f"<p><strong>🏛️ Registrar:</strong> {ipo.get('shareRegistrar', 'N/A')}</p>")
            if ipo.get('rating'):
                message_lines.append(f"<p><strong>⭐ Rating:</strong> {ipo.get('rating')}</p>")
            message_lines.append("<hr>")
    
    message_lines.append("<p><em>⚠️ Always do your own research before trading!</em></p>")
    
    message = "\n".join(message_lines)
    
    total_items = (
        (len(all_signals) if all_signals else 0)
    )
    print(f"📧 Sending summary email with {total_items} total items...")
    email_sender.send_email(subject, message)


async def main():
    # Group ID finder mode - uncomment to help find your group ID
    # Set this to True to just get group IDs and exit without running the main program
    find_group_id_mode = False
    
    if find_group_id_mode:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            print("\n==== TELEGRAM GROUP ID FINDER ====")
            print("Looking for group chats in recent bot messages...")
            
            if data["ok"] and data["result"]:
                for update in data["result"]:
                    if "message" in update and "chat" in update["message"]:
                        chat = update["message"]["chat"]
                        chat_id = chat["id"]
                        chat_type = chat["type"]
                        chat_title = chat.get("title", "Private Chat")
                        
                        print(f"Found: {chat_title} ({chat_type})")
                        print(f"ID: {chat_id}")
                        print("------------------------------")
            else:
                print("No messages found. Make sure to:")
                print("1. Add your bot to the group")
                print("2. Send a message in the group that mentions the bot")
                print("3. Run this script again")
            
            print("\nTo use this ID, update the tg_group_chat_ids line with your ID")
            print("==================================\n")
            return
        except Exception as e:
            print(f"Error finding group ID: {str(e)}")
            return

    
    signal_date = datetime.today().strftime('%Y-%m-%d')  # Format: 'YYYY-MM-DD'
    # signal_date = "2025-06-08"  # Uncomment to use a specific date

    # Initialize email sender using configuration
    email_sender = EmailSender()
    
    # Set up headers for data fetching
    base_url = "https://www.sharesansar.com/company/nhpc"
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.sharesansar.com',
        'referer': base_url,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    # Fetch cookies and CSRF token
    cookies, csrf_token = fetch_cookies_and_csrf_token(base_url, headers)
    headers = update_headers(headers, cookies, csrf_token)

    print("🚀 Starting MACD Signal Analysis...")
    print("="*60)
    print("PHASE 1: General Stock Analysis")
    print("="*60)

    # Load stock symbols from CSV
    with open("stock_list.csv", "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        stock_list = [row[0] for row in reader]

    # Filter company data
    filtered_data = load_company_data("company_data.json", stock_list)

    # Collect all signals for batch email
    all_signals = []
    # Collect low RSI alerts across all general stocks
    low_rsi_alerts = []

    for company in filtered_data:
        company_id = company["id"]
        company_symbol = company["symbol"].replace('/', '-')

        # Fetch and update price history!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        new_data = price_history(headers, company_id)
        update_csv(company_symbol, new_data)

        # Detect MACD signal code from here
        file_path = f"data/{company_symbol}.csv"

        data = pd.read_csv(file_path)
        # print(f"Detecting Signals for {company_symbol}")

        # Ensure column names are lowercase for consistency
        data.columns = [col.lower() for col in data.columns]

        # Extract relevant columns
        data = data[['published_date', 'close']]

        # Convert 'published_date' to datetime format for better handling
        data['published_date'] = pd.to_datetime(data['published_date'])

        # Ensure 'close' is numeric and handle missing values
        data['close'] = pd.to_numeric(data['close'], errors='coerce')
        data = data.dropna(subset=['close'])

        # Ensure data is sorted by date
        data = data.sort_values(by='published_date')

        # Calculate MACD and Signal line
        macd_data = calculate_macd(data)

        # Calculate RSI and collect low RSI alerts
        rsi_series = calculate_rsi_for_general_stocks(macd_data)
        if not rsi_series.empty and not pd.isna(rsi_series.iloc[-1]):
            latest_rsi = float(rsi_series.iloc[-1])
            latest_price = float(macd_data['close'].iloc[-1])
            if latest_rsi < RSI_LOW_ALERT_THRESHOLD:
                low_rsi_alerts.append({
                    'stock_symbol': company_symbol,
                    'rsi': latest_rsi,
                    'price': latest_price
                })

        # Detect intersections and collect signals
        intersections, signals_found = await detect_intersections(macd_data, company_symbol, signal_date, email_sender)
        all_signals.extend(signals_found)

    print("\n" + "="*60)
    print("PHASE 2: Personal Portfolio Analysis")
    print("="*60)
    
    # Initialize and run portfolio analysis with email sender
    portfolio_analyzer = PortfolioMACDAnalyzer(email_sender)
    
    # Analyze MACD signals for portfolio (now async)
    portfolio_signals = await portfolio_analyzer.analyze_portfolio_macd_signals()
    
    # Check RSI levels for personal stocks
    await portfolio_analyzer.check_personal_stocks_rsi()
    
    # Display detailed portfolio analysis
    portfolio_analyzer.display_portfolio_analysis()
    
    # Update CSV file with signals
    portfolio_analyzer.update_csv_with_signals()
    
    # Add portfolio signals to all signals
    if portfolio_signals:
        all_signals.extend(portfolio_signals)
    
    print("\n" + "="*60)
    print("PHASE 3: IPO Opportunity Check")
    print("="*60)
    
    # Initialize and run IPO checker
    ipo_checker = IPOChecker(email_sender)
    
    # Check for open IPOs and collect alerts
    ipo_alerts = await ipo_checker.check_and_notify_ipos()
    
    # Send summary email with all signals, IPO alerts, and low RSI opportunities
    if (all_signals or ipo_alerts or low_rsi_alerts) and email_sender:
        await send_summary_email(all_signals, email_sender, signal_date, ipo_alerts, low_rsi_alerts)
    
    print("\n🎉 Complete Analysis Finished!")
    print("✅ MACD signals analyzed and updated in 'my_portfolio.csv'")
    print("📧 Summary email sent with all signals!")
    print("🎯 IPO opportunities checked and notified if available!")

if __name__ == "__main__":
    asyncio.run(main())


