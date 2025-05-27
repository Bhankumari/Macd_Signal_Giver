import asyncio
import aiohttp
import requests
import json
import time

class BotTelegramSender:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.api_base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def get_updates(self):
        url = f"{self.api_base_url}/getUpdates"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"Failed to get updates. Status: {response.status}")
                    return None
    
    async def send_message(self, chat_id, message):
        url = f"{self.api_base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                if response.status == 200:
                    print(f"Message sent successfully to chat {chat_id}")
                    return True
                else:
                    response_text = await response.text()
                    print(f"Failed to send message to {chat_id}. Status: {response.status}. Response: {response_text}")
                    return False

async def main():
    # Your bot token
    bot_token = "7213295742:AAH8APqwSoXe-t0bElF9L_-ZOpebm2DTAM8"
    
    # Create bot sender
    bot = BotTelegramSender(bot_token)
    
    print("Bot Test Script")
    print("---------------")
    print("1. Start a chat with your bot in Telegram")
    print("2. Send a message to your bot")
    print("3. This script will respond and show your chat ID")
    print("4. If you've added the bot to a group, send a message in that group mentioning the bot")
    print("5. The script will also respond to group messages and show the group ID")
    print("\nWaiting for messages... (Press Ctrl+C to exit)")
    
    # Track chat IDs we've seen
    processed_updates = set()
    
    try:
        while True:
            # Get updates
            updates = await bot.get_updates()
            
            if updates and updates.get("ok", False):
                for update in updates.get("result", []):
                    update_id = update.get("update_id")
                    
                    # Skip already processed updates
                    if update_id in processed_updates:
                        continue
                    
                    processed_updates.add(update_id)
                    
                    # Check for a message
                    if "message" in update and "chat" in update["message"]:
                        chat = update["message"]["chat"]
                        chat_id = chat["id"]
                        chat_type = chat["type"]
                        
                        if chat_type == "private":
                            sender_name = update["message"]["from"]["first_name"]
                            print(f"\nReceived message from {sender_name} in private chat")
                            print(f"CHAT ID: {chat_id} (private)")
                            
                            # Send a response
                            await bot.send_message(chat_id, 
                                f"Hello {sender_name}! Your chat ID is: {chat_id}\n\n"
                                f"To use this ID, update your main.py file with:\n"
                                f"tg_group_chat_ids = [\"{chat_id}\"]")
                        
                        elif chat_type in ["group", "supergroup"]:
                            group_name = chat["title"]
                            print(f"\nReceived message from group: {group_name}")
                            print(f"GROUP CHAT ID: {chat_id} ({chat_type})")
                            
                            # Send a response
                            await bot.send_message(chat_id, 
                                f"Hello! This group's chat ID is: {chat_id}\n\n"
                                f"To use this ID, update your main.py file with:\n"
                                f"tg_group_chat_ids = [\"{chat_id}\"]")
            
            # Wait a bit before checking again
            await asyncio.sleep(2)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 