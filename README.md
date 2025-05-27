# MACD Signal Telegram Bot

This application fetches stock data, calculates MACD indicators, and sends buy/sell signals to a Telegram bot.

## Deployment on Render

1. Create a Render account at [render.com](https://render.com)
2. Connect your GitHub repository
3. Click "New" and select "Blueprint" 
4. Select your repository
5. Render will automatically detect the `render.yaml` file and configure the service
6. Add the following environment variables in Render:
   - `GITHUB_USERNAME`: Your GitHub username
   - `GITHUB_TOKEN`: A personal access token with repo permissions ([Create one here](https://github.com/settings/tokens))
7. Click "Apply"

The service will be deployed as a background worker that runs every day at 3:20 PM (except Friday and Sunday).

### Data Persistence

This application uses a Git-based approach for data persistence:
- After each run, updated stock data is committed back to your GitHub repository
- This ensures data persists between runs on Render's free tier
- The GitHub token must have permission to push to your repository

## Local Development

To run the application locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the worker (scheduled execution)
python worker.py

# Or run the main script directly (immediate execution)
python main.py
```

## Configuration

- Telegram Bot Token: Update in `main.py`
- Chat ID: Update in `main.py`
- Stock List: Update in `stock_list.csv` 