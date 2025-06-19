#!/bin/bash

# 🚀 Environment Setup Script for Telegram Trading Bot
# Run this script to set up your environment variables

echo "🔧 Setting up Telegram Bot Environment Variables..."

# Set the bot token (provided by user)
export TELEGRAM_BOT_TOKEN="7213295742:AAH8APqwSoXe-t0bElF9L_-ZOpebm2DTAM8"

# Set group chat ID (general signals only, no personal portfolio alerts)
export TELEGRAM_GROUP_CHAT_IDS="-1002500595333"

# Set personal chat ID (all alerts including personal portfolio)
export TELEGRAM_PERSONAL_CHAT_IDS="6595074511"

echo "✅ Environment variables set:"
echo "   Bot Token: ${TELEGRAM_BOT_TOKEN:0:10}...${TELEGRAM_BOT_TOKEN: -10}"
echo "   Group Chat IDs: $TELEGRAM_GROUP_CHAT_IDS"
echo "   Personal Chat IDs: $TELEGRAM_PERSONAL_CHAT_IDS"

echo ""
echo "🚀 To run the bot:"
echo "   python main.py"
echo ""
echo "🔍 To debug configuration:"
echo "   python debug_config.py"
echo ""
echo "💡 To make these permanent, add to your ~/.bashrc or ~/.zshrc:"
echo "   echo 'export TELEGRAM_BOT_TOKEN=\"7213295742:AAH8APqwSoXe-t0bElF9L_-ZOpebm2DTAM8\"' >> ~/.bashrc"
echo "   echo 'export TELEGRAM_GROUP_CHAT_IDS=\"-1002500595333\"' >> ~/.bashrc"
echo "   echo 'export TELEGRAM_PERSONAL_CHAT_IDS=\"6595074511\"' >> ~/.bashrc" 