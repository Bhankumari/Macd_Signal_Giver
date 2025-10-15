import requests
import json
import csv
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import asyncio
import aiohttp
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any
from email_config import (
    SMTP_EMAIL, SMTP_PASSWORD, RECIPIENT_EMAIL, SMTP_SERVER, SMTP_PORT,
    PORTFOLIO_STOCKS, EMAIL_TEMPLATES, RECIPIENT_EMAILS
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
        self.email_sender = email_sender
        
    def load_portfolio_from_csv(self, filename='my_portfolio.csv'):
        """Load portfolio data from CSV file"""
        try:
            df = pd.read_csv(filename)
            return df
        except FileNotFoundError:
            print(f"Portfolio file {filename} not found!")
            return None
    
    async def analyze_portfolio_macd_signals(self, signal_date_filter: str = None):
        """Analyze MACD signals for all stocks in portfolio. If signal_date_filter is provided (YYYY-MM-DD), only include signals on that date."""
        analysis_date = datetime.today().strftime('%Y-%m-%d')
        
        print(f"\n🔍 Analyzing Portfolio MACD signals for {analysis_date}...")
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
                # Optionally filter to an exact date (previous day requirement)
                if isinstance(recent_signals, list) and signal_date_filter:
                    recent_signals = [s for s in recent_signals if s['date'].strftime('%Y-%m-%d') == signal_date_filter]
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
            # Include only company symbol and price
            latest_price = signal.get('price') if isinstance(signal, dict) and 'price' in signal else None
            price_text = f"{latest_price}" if latest_price is not None else "N/A"
            message_lines.append(f"<p><strong>{stock}</strong>: ₹{price_text}</p>")
            
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
                    'signal': round(signal_current, 4),
                    'price': round(recent_data.loc[current_idx, 'close'], 2)
                })
            elif (macd_current < signal_current and macd_prev >= signal_prev):
                signals.append({
                    'type': 'SELL',
                    'date': date_current,
                    'macd': round(macd_current, 4),
                    'signal': round(signal_current, 4),
                    'price': round(recent_data.loc[current_idx, 'close'], 2)
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

async def detect_intersections(data, company_symbol, signal_date, email_sender):
    """Detect MACD crossovers and print signals (MACD only)."""
    intersections = []
    signals_found = []
    
    for i in range(1, len(data)):
        # Check for MACD crossing Signal line (Intersection)
        if (data['macd'].iloc[i] > data['signal'].iloc[i] and data['macd'].iloc[i - 1] <= data['signal'].iloc[i - 1]):
            # Buy signal: MACD crosses signal line from below
            intersections.append((data['published_date'].iloc[i], data['macd'].iloc[i], data['signal'].iloc[i], "Buy Signal", i))
        elif (data['macd'].iloc[i] < data['signal'].iloc[i] and data['macd'].iloc[i - 1] >= data['signal'].iloc[i - 1]):
            # Sell signal: MACD crosses signal line from above
            intersections.append((data['published_date'].iloc[i], data['macd'].iloc[i], data['signal'].iloc[i], "Sell Signal", i))

    # Print intersection points and signal types with RSI information
    for date, macd_val, signal_val, signal_type, index in intersections:
        # Define today's date in the same format as the 'date' variable
        today_date = datetime.strptime(f"{signal_date} 00:00:00", "%Y-%m-%d %H:%M:%S")

        # Convert 'date' to datetime for consistent comparison
        intersection_date = datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")

        if intersection_date == today_date:
            current_price = data['close'].iloc[index]
            
            # Print MACD-only signal
            print(f"\n\n{signal_type}: {company_symbol} | Price: {current_price:.2f} ({intersection_date.strftime('%Y-%m-%d')})")
            
            # Collect signal for batch email (MACD only)
            signals_found.append({
                'signal_type': signal_type,
                'stock_symbol': company_symbol,
                'price': current_price,
                'date': intersection_date.strftime('%Y-%m-%d'),
                'macd': macd_val,
                'signal': signal_val
            })

    return intersections, signals_found


async def send_summary_email(all_signals, email_sender, signal_date):
    """Send a summary email with MACD signals only."""
    has_signals = all_signals and len(all_signals) > 0
    
    if not has_signals:
        return
    
    # Count signals by type
    buy_signals = [s for s in all_signals if s['signal_type'] == 'Buy Signal']
    sell_signals = [s for s in all_signals if s['signal_type'] == 'Sell Signal']
    
    subject = f"📊 Market Analysis Summary - {signal_date}"
    
    # Create summary message
    message_lines = [
        f"<h1>📊 Market Analysis Summary Report</h1>",
        f"<p><strong>Date:</strong> {signal_date}</p>",
        "<hr>"
    ]
    
    if has_signals:
        message_lines.extend([
            f"<h2>📈 MACD Signals</h2>",
            "<hr>"
        ])
        
        if buy_signals:
            message_lines.append("<h3>🟢 Buy Signals</h3>")
            for signal in buy_signals:
                price_text = f"{signal['price']:.2f}" if signal.get('price') is not None else "N/A"
                message_lines.append(f"<p><strong>{signal['stock_symbol']}</strong>: ₹{price_text}</p>")
            message_lines.append("<hr>")
        
        if sell_signals:
            message_lines.append("<h3>🔴 Sell Signals</h3>")
            for signal in sell_signals:
                price_text = f"{signal['price']:.2f}" if signal.get('price') is not None else "N/A"
                message_lines.append(f"<p><strong>{signal['stock_symbol']}</strong>: ₹{price_text}</p>")
            message_lines.append("<hr>")

    message_lines.append("<p><em>⚠️ Always do your own research before trading!</em></p>")
    
    message = "\n".join(message_lines)
    
    print(f"📧 Sending summary email with {len(all_signals)} MACD signals...")
    email_sender.send_email(subject, message)


async def run_analysis_for_date(signal_date: str, fast_mode: bool = False):
    # signal_date is provided by caller (YYYY-MM-DD)

    # Initialize email sender using configuration
    email_sender = EmailSender()
    
    if not fast_mode:
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
    else:
        print("⚡ Fast mode enabled - skipping data fetching")

    print("🚀 Starting MACD Signal Analysis...")
    print("="*60)
    print("PHASE 1: General Stock Analysis")
    print("="*60)

    # Load stock symbols from CSV
    with open("stock_list.csv", "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        stock_list = [row[0] for row in reader]

    # In fast mode, limit to first 10 stocks for faster execution
    if fast_mode:
        stock_list = stock_list[:10]
        print(f"⚡ Fast mode: Processing only first {len(stock_list)} stocks")

    # Filter company data
    filtered_data = load_company_data("company_data.json", stock_list)

    # Collect all signals for batch email
    all_signals = []
    # No RSI alerts collection; focusing on MACD only

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

        # Skip RSI calculation; MACD-only workflow

        # Detect intersections and collect signals
        intersections, signals_found = await detect_intersections(macd_data, company_symbol, signal_date, email_sender)
        all_signals.extend(signals_found)

    print("\n" + "="*60)
    print("PHASE 2: Personal Portfolio Analysis")
    print("="*60)
    
    # Initialize and run portfolio analysis with email sender
    portfolio_analyzer = PortfolioMACDAnalyzer(email_sender)
    
    # Analyze MACD signals for portfolio (now async)
    # Filter portfolio signals strictly to the provided signal_date
    portfolio_signals = await portfolio_analyzer.analyze_portfolio_macd_signals(signal_date_filter=signal_date)
    
    # Display detailed portfolio analysis
    portfolio_analyzer.display_portfolio_analysis()
    
    # Update CSV file with signals
    portfolio_analyzer.update_csv_with_signals()
    
    # Add portfolio signals to all signals
    if portfolio_signals:
        all_signals.extend(portfolio_signals)
    
    # Send summary email with MACD signals only
    if all_signals and email_sender:
        await send_summary_email(all_signals, email_sender, signal_date)
    
    print("\n🎉 Complete Analysis Finished!")
    print("✅ MACD signals analyzed and updated in 'my_portfolio.csv'")
    print("📧 Summary email sent with MACD signals!")


async def scheduler_loop():
    """Run analysis daily at 11:00 Asia/Kathmandu for previous day's signals."""
    tz = ZoneInfo("Asia/Kathmandu")
    print("⏰ Scheduler started for 11:00 Asia/Kathmandu daily run (previous day's MACD crossovers).")
    while True:
        now_ktm = datetime.now(tz)
        target_today = now_ktm.replace(hour=11, minute=0, second=0, microsecond=0)
        if now_ktm >= target_today:
            next_run = target_today + timedelta(days=1)
        else:
            next_run = target_today
        seconds_until = (next_run - now_ktm).total_seconds()
        next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S %Z')
        print(f"⏳ Next run at: {next_run_str} (in {int(seconds_until)} seconds)")
        await asyncio.sleep(seconds_until)
        # Determine previous day in Kathmandu time
        run_day = (datetime.now(tz) - timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"🚀 Running scheduled analysis for previous day: {run_day} (Asia/Kathmandu)")
        try:
            await run_analysis_for_date(run_day)
        except Exception as e:
            print(f"❌ Scheduled run failed: {str(e)}")


async def main():
    # Mode: schedule daily at 11:00 Asia/Kathmandu, unless ONE_SHOT=1
    one_shot = os.getenv('ONE_SHOT', '0') == '1'
    fast_mode = os.getenv('FAST_MODE', '0') == '1'  # Enable fast mode for CI/CD
    if one_shot:
        tz = ZoneInfo("Asia/Kathmandu")
        signal_date = (datetime.now(tz) - timedelta(days=1)).strftime('%Y-%m-%d')
        await run_analysis_for_date(signal_date, fast_mode=fast_mode)
    else:
        await scheduler_loop()

if __name__ == "__main__":
    asyncio.run(main())
