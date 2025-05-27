import asyncio
import time
import schedule
import logging
from datetime import datetime
import main  # Import your main script
import git_utils  # Import our Git utilities

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_main_script():
    # Check if today is Friday (4) or Sunday (6)
    day_of_week = datetime.now().weekday()
    if day_of_week in [4, 6]:  # Skip Friday and Sunday
        logger.info(f"Today is {'Friday' if day_of_week == 4 else 'Sunday'}, skipping execution")
        return
    
    logger.info(f"Starting main script at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await main.main()
    logger.info(f"Finished execution at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Commit and push changes to the repository
    logger.info("Committing data changes back to the repository")
    if git_utils.commit_and_push_changes():
        logger.info("Successfully committed and pushed data updates")
    else:
        logger.error("Failed to commit and push data updates")

def job():
    asyncio.run(run_main_script())

def main_loop():
    # Configure Git
    logger.info("Setting up Git configuration")
    git_utils.setup_git_config()
    
    # Schedule job at 3:20 PM every day
    schedule.every().day.at("15:20").do(job)
    
    logger.info("Worker started. Will run at 3:20 PM every day except Friday and Sunday.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main_loop() 