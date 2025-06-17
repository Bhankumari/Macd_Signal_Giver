# GitHub Actions Setup for MACD Signal

This guide explains how to set up automatic daily execution of your MACD Signal script using GitHub Actions.

## Setup Steps

### 1. Push your code to GitHub
First, make sure your repository is on GitHub with all the files.

### 2. Add GitHub Secrets
You need to add your sensitive credentials as GitHub Secrets:

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** for each of the following:

**Required Secrets:**
- **Name:** `TELEGRAM_BOT_TOKEN`
  **Value:** Your Telegram bot token (e.g., `7213295742:AAH8APqwSoXe-t0bElF9L_-ZOpebm2DTAM8`)

- **Name:** `TELEGRAM_GROUP_CHAT_IDS`  
  **Value:** Your group chat ID (e.g., `-1002500595333`)
  **Description:** Group chat that receives general stock signals and IPO alerts (NO personal portfolio alerts)

- **Name:** `TELEGRAM_PERSONAL_CHAT_IDS`  
  **Value:** Your personal chat ID (e.g., `6595074511`)
  **Description:** Personal chat that receives ALL alerts including personal portfolio notifications

### 3. Configure Schedule Timezone
The workflow is currently set to run at **3:20 PM UTC** daily.

**To adjust for your timezone:**
- Edit `.github/workflows/macd-signal.yml`
- Change the cron expression in line 8:
  ```yaml
  - cron: '20 15 * * *'  # This is 3:20 PM UTC
  ```

**Common timezone conversions for 3:20 PM local time:**
- **Nepal Time (UTC+5:45):** `'20 09 * * *'` (9:20 AM UTC)
- **India Time (UTC+5:30):** `'50 09 * * *'` (9:50 AM UTC)  
- **US Eastern (UTC-5):** `'20 20 * * *'` (8:20 PM UTC)
- **US Pacific (UTC-8):** `'20 23 * * *'` (11:20 PM UTC)

### 4. Enable Actions
1. Go to the **Actions** tab in your repository
2. If Actions are disabled, click **Enable Actions**
3. The workflow will appear and can be triggered manually or wait for the scheduled time

### 5. Manual Testing
To test the workflow immediately:
1. Go to **Actions** tab
2. Click on **MACD Signal Daily Runner**
3. Click **Run workflow** button
4. Click the green **Run workflow** button

## How it Works

The GitHub Action will:
1. **Run daily at 11:40 AM UTC** (or your configured time)
2. **Fetch latest stock data** from sharesansar.com
3. **Calculate MACD indicators** for all stocks in your list
4. **Detect buy/sell signals** for the current date
5. **Send Telegram notifications** with smart routing:
   - **Group Chat**: General stock signals + IPO alerts (NO personal portfolio)
   - **Personal Chat**: General stock signals + Personal portfolio alerts + IPO alerts
6. **Update CSV files** with new data
7. **Commit and push** updated data back to the repository

## Monitoring

- Check the **Actions** tab to see workflow runs
- View logs for each run to debug any issues
- Failed runs will show error details in the logs

## File Structure
```
.
├── .github/
│   └── workflows/
│       └── macd-signal.yml      # GitHub Actions workflow
├── data/                        # Stock data CSV files (auto-created)
├── main.py                      # Main script
├── requirements.txt             # Python dependencies
├── stock_list.csv              # List of stocks to monitor
└── company_data.json           # Company data (auto-created)
```

## Security Notes
- Never commit your bot token or chat IDs to the repository
- Always use GitHub Secrets for sensitive data
- The workflow only has access to secrets you explicitly configure 