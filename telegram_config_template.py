"""
Telegram Bot Configuration Template
===================================

STEP 1: Find your Personal Chat ID
==================================
1. Start a private chat with your bot
2. Send any message to the bot (like "hello")
3. Run: python find_chat_id.py
4. Look for "Private Chat" entry and copy the ID

STEP 2: Set Environment Variables
=================================
Set these environment variables (or update the defaults in main.py):

# Your bot token (same for all chats)
TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Group chat ID - Only receives general stock signals (NOT personal portfolio alerts)
TELEGRAM_GROUP_CHAT_IDS="-1002500595333"

# Personal chat ID - Receives ALL alerts including personal portfolio
TELEGRAM_PERSONAL_CHAT_IDS="6595074511"

STEP 3: Test Configuration
=========================
After setting up:
- Group chat (-1002500595333) will get: General stock signals + IPO alerts
- Personal chat (6595074511) will get: General stock signals + Personal portfolio alerts + IPO alerts

STEP 4: Multiple Chat IDs (Optional)
===================================
You can add multiple IDs separated by commas:
TELEGRAM_GROUP_CHAT_IDS="6595074511,another_group_id"
TELEGRAM_PERSONAL_CHAT_IDS="your_personal_id,family_member_id"

CONFIGURATION SUMMARY:
=====================
📱 Group Chat (-1002500595333):
   ✅ General stock MACD signals
   ✅ IPO notifications
   ❌ Personal portfolio alerts

📱 Personal Chat (6595074511):
   ✅ General stock MACD signals
   ✅ IPO notifications
   ✅ Personal portfolio alerts (GBIME, RURU, HBL, ICFC, JBLB, JFL, UPPER)
"""

# If running locally, you can set the values directly here instead of environment variables:
LOCAL_CONFIG = {
    "TELEGRAM_BOT_TOKEN": "your_bot_token_here",
    "TELEGRAM_GROUP_CHAT_IDS": "-1002500595333",  # Your group chat ID
    "TELEGRAM_PERSONAL_CHAT_IDS": "6595074511"  # Your personal chat ID
} 