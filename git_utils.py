import os
import subprocess
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_git_config():
    """Set up Git configuration for the worker."""
    try:
        # Set Git identity (use environment variables or defaults)
        git_email = os.environ.get("GIT_USER_EMAIL", "macd-signal-bot@render.com")
        git_name = os.environ.get("GIT_USER_NAME", "MACD Signal Bot")
        
        subprocess.run(["git", "config", "--global", "user.email", git_email])
        subprocess.run(["git", "config", "--global", "user.name", git_name])
        
        # Configure token-based authentication if credentials are provided
        git_token = os.environ.get("GITHUB_TOKEN")
        git_username = os.environ.get("GITHUB_USERNAME")
        
        if git_token and git_username:
            repo_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode().strip()
            if repo_url.startswith("https://"):
                new_url = f"https://{git_username}:{git_token}@github.com/{repo_url.split('github.com/')[1]}"
                subprocess.run(["git", "remote", "set-url", "origin", new_url])
                logger.info("Configured Git with token authentication")
            
        return True
    except Exception as e:
        logger.error(f"Error setting up Git config: {str(e)}")
        return False

def commit_and_push_changes():
    """Commit and push data changes back to the repository."""
    try:
        # Check if there are any changes
        status = subprocess.check_output(["git", "status", "--porcelain"]).decode()
        
        if not status.strip():
            logger.info("No changes to commit")
            return True
        
        # Get the current date for the commit message
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Add all changes in the data directory
        subprocess.run(["git", "add", "data/"])
        
        # Commit the changes
        commit_message = f"Update stock data - {current_date}"
        subprocess.run(["git", "commit", "-m", commit_message])
        
        # Push the changes
        subprocess.run(["git", "push", "origin", "main"])
        
        logger.info(f"Successfully committed and pushed changes: {commit_message}")
        return True
    except Exception as e:
        logger.error(f"Error committing changes: {str(e)}")
        return False 