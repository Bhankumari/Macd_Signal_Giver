import requests
import json
import csv
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import asyncio
import aiohttp
import os
from typing import Dict, List, Any

class BotTelegramSender:
    def __init__(self, bot_token, chat_ids):
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    async def send_message(self, message):
        async with aiohttp.ClientSession() as session:
            for chat_id in self.chat_ids:
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                async with session.post(self.api_url, data=payload) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        print(f"Failed to send message to {chat_id}. Status: {response.status}. Response: {response_text}")
                    else:
                        print(f"Message sent successfully to chat {chat_id}")

class PortfolioMACDAnalyzer:
    def __init__(self, tg_bot_token=None, tg_group_chat_ids=None):
        self.my_stocks = ['GBIME', 'RURU', 'HBL', 'ICFC', 'JBLB', 'JFL', 'UPPER','TVCL','BHDC']
        self.portfolio_data = []
        self.macd_signals = {}
        self.tg_bot_token = tg_bot_token
        self.tg_group_chat_ids = tg_group_chat_ids
        
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
        
        # Send Telegram messages for portfolio signals
        if portfolio_signals_found and self.tg_bot_token and self.tg_group_chat_ids:
            await self.send_portfolio_telegram_messages(portfolio_signals_found)
    
    async def send_portfolio_telegram_messages(self, portfolio_signals):
        """Send Telegram messages for portfolio stocks with MACD signals"""
        for signal_info in portfolio_signals:
            stock = signal_info['stock']
            signal = signal_info['signal']
            signal_type = signal['type']
            date = signal['date'].strftime('%Y-%m-%d')
            
            # Create message for user's portfolio stocks
            if signal_type == 'BUY':
                message = f"🟢 Your Stock Alert: {stock} - BUY SIGNAL detected on {date}\nMACD: {signal['macd']} | Signal Line: {signal['signal']}\n📈 Consider reviewing your position!"
            else:
                message = f"🔴 Your Stock Alert: {stock} - SELL SIGNAL detected on {date}\nMACD: {signal['macd']} | Signal Line: {signal['signal']}\n📉 Consider reviewing your position!"
            
            print(f"📱 Sending portfolio alert for {stock}...")
            await send_messages_with_bot(self.tg_bot_token, self.tg_group_chat_ids, message)

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

class IPOChecker:
    def __init__(self, tg_bot_token=None, tg_group_chat_ids=None):
        self.tg_bot_token = tg_bot_token
        self.tg_group_chat_ids = tg_group_chat_ids
    
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

    def format_ipo_for_telegram(self, ipo: Dict[str, Any]) -> str:
        """
        Format IPO details for Telegram message
        """
        message = f"🎯 <b>Open IPO Alert!</b>\n\n"
        message += f"🏢 <b>Company:</b> {ipo.get('companyName', 'Unknown Company')}\n"
        message += f"📈 <b>Symbol:</b> {ipo.get('stockSymbol', 'N/A')}\n"
        message += f"🏭 <b>Sector:</b> {ipo.get('sectorName', 'N/A')}\n"
        message += f"💰 <b>Price per Unit:</b> Rs. {ipo.get('pricePerUnit', 'N/A')}\n"
        message += f"📊 <b>Min Units:</b> {ipo.get('minUnits', 'N/A')}\n"
        message += f"📊 <b>Max Units:</b> {ipo.get('maxUnits', 'N/A')}\n"
        message += f"💼 <b>Total Amount:</b> Rs. {ipo.get('totalAmount', 'N/A')}\n"
        message += f"📅 <b>Opens:</b> {ipo.get('openingDateAD', 'N/A')}\n"
        message += f"📅 <b>Closes:</b> {ipo.get('closingDateAD', 'N/A')}\n"
        message += f"🏛️ <b>Registrar:</b> {ipo.get('shareRegistrar', 'N/A')}\n"
        if ipo.get('rating'):
            message += f"⭐ <b>Rating:</b> {ipo.get('rating')}\n"
        message += f"\n💡 <i>Don't miss this investment opportunity!</i>"
        
        return message

    async def check_and_notify_ipos(self):
        """
        Check for open IPOs and send Telegram notifications
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
            
            # Send Telegram notifications for each open IPO
            if self.tg_bot_token and self.tg_group_chat_ids:
                for ipo in open_ipos:
                    message = self.format_ipo_for_telegram(ipo)
                    print(f"📱 Sending IPO alert for {ipo.get('companyName', 'Unknown')}...")
                    await send_messages_with_bot(self.tg_bot_token, self.tg_group_chat_ids, message)
            
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


async def detect_intersections(data, company_symbol, signal_date, tg_bot_token, tg_group_chat_ids):
    """Function to detect MACD crossovers and print signals"""
    intersections = []

    for i in range(1, len(data)):
        # Check for MACD crossing Signal line (Intersection)
        if (data['macd'].iloc[i] > data['signal'].iloc[i] and data['macd'].iloc[i - 1] <= data['signal'].iloc[i - 1]):
            # Buy signal: MACD crosses signal line from below
            intersections.append((data['published_date'].iloc[i], data['macd'].iloc[i], data['signal'].iloc[i], "Buy Signal"))
        elif (data['macd'].iloc[i] < data['signal'].iloc[i] and data['macd'].iloc[i - 1] >= data['signal'].iloc[i - 1]):
            # Sell signal: MACD crosses signal line from above
            intersections.append((data['published_date'].iloc[i], data['macd'].iloc[i], data['signal'].iloc[i], "Sell Signal"))

    # Print intersection points and signal types
    for date, macd_val, signal_val, signal_type in intersections:
        # Define today's date in the same format as the 'date' variable
        today_date = datetime.strptime(f"{signal_date} 00:00:00", "%Y-%m-%d %H:%M:%S")

        # Convert 'date' to datetime for consistent comparison
        intersection_date = datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")

        if intersection_date == today_date:
            # Choose color based on signal type
            if signal_type == "Buy Signal":
                signal_color = "\033[92m"  # Green for Buy Signal
            elif signal_type == "Sell Signal":
                signal_color = "\033[91m"  # Red for Sell Signal
            else:
                signal_color = "\033[0m"  # Default (no color)

            symbol_color = "\033[94m\033[1m"  # Blue and bold for company symbol
            reset_color = "\033[0m"  # Reset to default color

            # Simplified print statement - only signal type and company name
            print(f"\n\n{signal_type}: {company_symbol} ({intersection_date.strftime('%Y-%m-%d')})")
        
            # Simplified message - only signal type and company name
            message = f"{signal_type}: {company_symbol} ({intersection_date.strftime('%Y-%m-%d')})"

            # Uncomment the following line to enable Telegram messages
            await send_messages_with_bot(tg_bot_token, tg_group_chat_ids, message)

    return intersections


async def send_messages_with_bot(bot_token, group_chat_ids, message):
    bot_sender = BotTelegramSender(bot_token, group_chat_ids)
    try:
        await bot_sender.send_message(message)
    except Exception as e:
        print(f"Error while trying to send message: {str(e)}")

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

    # Get credentials from environment variables (for GitHub Actions) or use defaults for local testing
    tg_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    tg_group_chat_ids_str = os.getenv("TELEGRAM_CHAT_IDS", "YOUR_CHAT_ID_HERE")
    tg_group_chat_ids = [chat_id.strip() for chat_id in tg_group_chat_ids_str.split(",")]

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

        # Detect intersections and print signals
        await detect_intersections(macd_data, company_symbol, signal_date, tg_bot_token, tg_group_chat_ids)

    print("\n" + "="*60)
    print("PHASE 2: Personal Portfolio Analysis")
    print("="*60)
    
    # Initialize and run portfolio analysis with Telegram credentials
    portfolio_analyzer = PortfolioMACDAnalyzer(tg_bot_token, tg_group_chat_ids)
    
    # Analyze MACD signals for portfolio (now async)
    await portfolio_analyzer.analyze_portfolio_macd_signals()
    
    # Display detailed portfolio analysis
    portfolio_analyzer.display_portfolio_analysis()
    
    # Update CSV file with signals
    portfolio_analyzer.update_csv_with_signals()
    
    print("\n" + "="*60)
    print("PHASE 3: IPO Opportunity Check")
    print("="*60)
    
    # Initialize and run IPO checker
    ipo_checker = IPOChecker(tg_bot_token, tg_group_chat_ids)
    
    # Check for open IPOs and send notifications
    await ipo_checker.check_and_notify_ipos()
    
    print("\n🎉 Complete Analysis Finished!")
    print("✅ MACD signals analyzed and updated in 'my_portfolio.csv'")
    print("📱 Portfolio alerts sent to Telegram if signals detected!")
    print("🎯 IPO opportunities checked and notified if available!")

if __name__ == "__main__":
    asyncio.run(main())
