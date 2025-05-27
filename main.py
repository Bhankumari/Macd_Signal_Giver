import requests
import json
import csv
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import asyncio
import aiohttp

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
        bot_token = "7213295742:AAH8APqwSoXe-t0bElF9L_-ZOpebm2DTAM8"
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
    
    # Use today's date for testing
   #signal_date = datetime.today().strftime('%Y-%m-%d')  # Format: 'YYYY-MM-DD'
    signal_date = "2025-05-26"  # Uncomment to use a specific date

    tg_bot_token = "7213295742:AAH8APqwSoXe-t0bElF9L_-ZOpebm2DTAM8"
    # Using the chat ID we found from the test script
    tg_group_chat_ids = ["6595074511"]  # This is the chat ID we found

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
       # new_data = price_history(headers, company_id)
        #update_csv(company_symbol, new_data)

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

if __name__ == "__main__":
    asyncio.run(main())