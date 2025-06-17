# Migration Guide: Single Chat ID → Dual Chat ID System

## 🔄 **What Changed?**

The bot now supports **TWO SEPARATE CHAT CONFIGURATIONS**:

### Before (Old System)
- ❌ Single `TELEGRAM_CHAT_IDS` sent all alerts to all chats
- ❌ No way to separate personal portfolio alerts from general signals

### After (New System)  
- ✅ `TELEGRAM_GROUP_CHAT_IDS` for general signals only
- ✅ `TELEGRAM_PERSONAL_CHAT_IDS` for all alerts including personal portfolio
- ✅ Smart message routing based on chat type

## 📋 **Migration Steps**

### Step 1: Update GitHub Secrets
**Remove the old secret:**
1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. **Delete:** `TELEGRAM_CHAT_IDS` (old secret)

**Add new secrets:**
3. **Add:** `TELEGRAM_GROUP_CHAT_IDS` with value `-1002500595333`
4. **Add:** `TELEGRAM_PERSONAL_CHAT_IDS` with value `6595074511`
5. **Keep:** `TELEGRAM_BOT_TOKEN` (unchanged)

### Step 2: Update Local Environment (if running locally)
**Replace your old environment variables:**
```bash
# OLD - Remove these
unset TELEGRAM_CHAT_IDS

# NEW - Add these
export TELEGRAM_GROUP_CHAT_IDS="-1002500595333"
export TELEGRAM_PERSONAL_CHAT_IDS="6595074511"
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

### Step 3: Verify Configuration
After migration, verify your setup:

**Group Chat (-1002500595333) will receive:**
- ✅ General stock MACD signals (all stocks from stock_list.csv)
- ✅ IPO notifications
- ❌ Personal portfolio alerts (GBIME, RURU, HBL, ICFC, JBLB, JFL, UPPER)

**Personal Chat (6595074511) will receive:**
- ✅ General stock MACD signals (all stocks from stock_list.csv)  
- ✅ IPO notifications
- ✅ Personal portfolio alerts (GBIME, RURU, HBL, ICFC, JBLB, JFL, UPPER)

## 🧪 **Testing**

After migration, test your configuration:
1. Go to GitHub Actions → "MACD Signal Daily Runner"
2. Click "Run workflow" to trigger manually
3. Check both chats receive appropriate messages

## ❓ **Troubleshooting**

**Issue:** No messages received in group chat
- **Solution:** Check `TELEGRAM_GROUP_CHAT_IDS` secret is set correctly

**Issue:** No personal portfolio alerts received  
- **Solution:** Check `TELEGRAM_PERSONAL_CHAT_IDS` secret is set correctly

**Issue:** Duplicate messages in personal chat
- **Solution:** This is expected - personal chat gets both general + portfolio alerts

## 📞 **Support**

If you encounter issues:
1. Check GitHub Actions logs for errors
2. Verify all three secrets are properly set
3. Ensure both chat IDs are correct and bot has access to both chats 