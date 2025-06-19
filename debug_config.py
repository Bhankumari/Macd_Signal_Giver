#!/usr/bin/env python3
"""
Debug Configuration Script
Helps verify your Telegram bot configuration
"""

import os

def check_environment_variables():
    """Check and display environment variable configuration"""
    
    print("🔍 CONFIGURATION DEBUG TOOL")
    print("=" * 50)
    
    # Check bot token
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "NOT_SET")
    if bot_token == "NOT_SET" or bot_token == "YOUR_BOT_TOKEN_HERE":
        print("❌ TELEGRAM_BOT_TOKEN: Not properly set")
    else:
        print(f"✅ TELEGRAM_BOT_TOKEN: {bot_token[:10]}...{bot_token[-10:]} (partially hidden)")
    
    # Check group chat IDs
    group_ids_str = os.getenv("TELEGRAM_GROUP_CHAT_IDS", "NOT_SET")
    if group_ids_str == "NOT_SET":
        print("❌ TELEGRAM_GROUP_CHAT_IDS: Not set")
    else:
        group_ids = [chat_id.strip() for chat_id in group_ids_str.split(",") if chat_id.strip()]
        print(f"✅ TELEGRAM_GROUP_CHAT_IDS: {group_ids}")
    
    # Check personal chat IDs
    personal_ids_str = os.getenv("TELEGRAM_PERSONAL_CHAT_IDS", "NOT_SET")
    if personal_ids_str == "NOT_SET":
        print("❌ TELEGRAM_PERSONAL_CHAT_IDS: Not set")
    else:
        personal_ids = [chat_id.strip() for chat_id in personal_ids_str.split(",") if chat_id.strip()]
        print(f"✅ TELEGRAM_PERSONAL_CHAT_IDS: {personal_ids}")
    
    print("\n" + "=" * 50)
    print("📋 CONFIGURATION SUMMARY:")
    
    # Process and validate
    group_ids = []
    personal_ids = []
    
    if group_ids_str != "NOT_SET":
        group_ids = [cid.strip() for cid in group_ids_str.split(",") if cid.strip() and cid.strip() != 'YOUR_CHAT_ID_HERE']
    
    if personal_ids_str != "NOT_SET":
        personal_ids = [cid.strip() for cid in personal_ids_str.split(",") if cid.strip() and cid.strip() != 'YOUR_PERSONAL_CHAT_ID_HERE']
    
    all_ids = group_ids + personal_ids
    
    print(f"Group Chat IDs: {len(group_ids)} found")
    for i, gid in enumerate(group_ids, 1):
        print(f"  {i}. {gid}")
    
    print(f"Personal Chat IDs: {len(personal_ids)} found")
    for i, pid in enumerate(personal_ids, 1):
        print(f"  {i}. {pid}")
    
    print(f"Total Valid Chat IDs: {len(all_ids)}")
    
    # Recommendations
    print("\n" + "=" * 50)
    print("💡 RECOMMENDATIONS:")
    
    if not all_ids:
        print("❌ No valid chat IDs found!")
        print("   Set environment variables:")
        print("   export TELEGRAM_GROUP_CHAT_IDS='-1002500595333'")
        print("   export TELEGRAM_PERSONAL_CHAT_IDS='6595074511'")
    elif len(all_ids) == 1:
        print("⚠️  Only one chat ID configured")
        print("   Consider setting both group and personal chat IDs")
    else:
        print("✅ Configuration looks good!")
    
    if bot_token in ["NOT_SET", "YOUR_BOT_TOKEN_HERE"]:
        print("❌ Bot token not set!")
        print("   Set: export TELEGRAM_BOT_TOKEN='your_actual_bot_token'")

def test_chat_id_parsing():
    """Test the chat ID parsing logic"""
    
    print("\n" + "=" * 50)
    print("🧪 TESTING CHAT ID PARSING:")
    
    # Test cases
    test_cases = [
        "-1002500595333",
        "6595074511",  
        "-1002500595333,6595074511",
        "-1002500595333, 6595074511 ",
        "",
        "YOUR_CHAT_ID_HERE",
        "123,456,789"
    ]
    
    for test_case in test_cases:
        print(f"\nInput: '{test_case}'")
        parsed = [chat_id.strip() for chat_id in test_case.split(",") if chat_id.strip()]
        filtered = [cid for cid in parsed if cid and cid not in ['YOUR_CHAT_ID_HERE', 'YOUR_PERSONAL_CHAT_ID_HERE']]
        print(f"Parsed: {parsed}")
        print(f"Filtered: {filtered}")

if __name__ == "__main__":
    check_environment_variables()
    test_chat_id_parsing()
    
    print("\n" + "=" * 50)
    print("🚀 QUICK FIX COMMANDS:")
    print("For local testing, run:")
    print("export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
    print("export TELEGRAM_GROUP_CHAT_IDS='-1002500595333'")
    print("export TELEGRAM_PERSONAL_CHAT_IDS='6595074511'")
    print("python main.py") 