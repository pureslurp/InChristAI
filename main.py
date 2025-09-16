"""
Main application for InChrist AI Twitter Bot
"""
import logging
import schedule
import time
import sys
import signal
import os
from datetime import datetime

# Use cloud config if available, fallback to local config
try:
    cloud_deployment = os.getenv('CLOUD_DEPLOYMENT')
    port_set = os.getenv('PORT')
    print(f"DEBUG: CLOUD_DEPLOYMENT={cloud_deployment}, PORT={port_set}")
    
    if cloud_deployment or port_set:
        import config_cloud as config
        print("DEBUG: Successfully imported config_cloud")
        logger_setup = logging.getLogger(__name__)
        logger_setup.info("Using cloud configuration")
    else:
        import config
        print("DEBUG: Using local config (no cloud env vars)")
        logger_setup = logging.getLogger(__name__)
        logger_setup.info("Using local configuration")
except ImportError as e:
    print(f"DEBUG: ImportError when loading config: {e}")
    import config
    logger_setup = logging.getLogger(__name__)
    logger_setup.info("Using local configuration (cloud config not found)")

from twitter_api import TwitterAPI
from daily_poster import DailyPoster
from interaction_handler import InteractionHandler
from web_server import start_health_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inchrist_ai.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class InChristAI:
    def __init__(self, dry_run=False):
        self.twitter_api = TwitterAPI(dry_run=dry_run)
        self.daily_poster = DailyPoster(dry_run=dry_run)
        self.interaction_handler = InteractionHandler(dry_run=dry_run)
        self.running = False
        self.dry_run = dry_run
        self.web_server = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.web_server:
            self.web_server.stop()

    def start(self):
        """Start the bot with scheduled tasks"""
        try:
            # Verify Twitter API credentials
            if not self.twitter_api.verify_credentials():
                logger.error("Failed to verify Twitter credentials. Please check your API keys.")
                return False

            logger.info("InChrist AI Bot starting up...")
            
            # Start health check web server for cloud deployment
            if hasattr(config, 'PORT'):
                self.web_server = start_health_server(self, config.PORT)
            
            # Schedule daily verse posting
            posting_time = config.POSTING_TIME
            logger.info(f"DEBUG: Raw posting_time from config: '{posting_time}' (type: {type(posting_time)})")
            
            # Ensure proper time format (convert 8:00 to 08:00 format)
            if isinstance(posting_time, str):
                posting_time = posting_time.strip()
                # Handle both H:MM and HH:MM formats
                if ':' in posting_time:
                    time_parts = posting_time.split(':')
                    if len(time_parts) == 2:
                        hour, minute = time_parts
                        # Add leading zero to hour if needed
                        hour = hour.zfill(2)
                        minute = minute.zfill(2)
                        posting_time = f"{hour}:{minute}"
                        logger.info(f"DEBUG: Normalized time format: {posting_time}")
                    else:
                        logger.warning(f"DEBUG: Invalid time format: {posting_time}, using default 08:00")
                        posting_time = "08:00"
                else:
                    logger.warning(f"DEBUG: No colon in time format: {posting_time}, using default 08:00")
                    posting_time = "08:00"
            else:
                logger.warning(f"DEBUG: posting_time is not a string: {posting_time}, using default 08:00")
                posting_time = "08:00"
            
            schedule.every().day.at(posting_time).do(self._post_daily_verse)
            logger.info(f"Scheduled daily verse posting at {posting_time}")
            
            # Check mentions once on startup for testing
            logger.info("Checking mentions on startup for testing...")
            self._check_mentions()
            
            # Schedule mention checking every 6 hours (more reliable than fixed times)
            schedule.every(6).hours.do(self._check_mentions)
            logger.info("Scheduled mention checking every 6 hours to stay within API quota")
            
            # Schedule daily cleanup at midnight
            schedule.every().day.at("00:00").do(self._daily_cleanup)
            logger.info("Scheduled daily cleanup at midnight")
            
            # Schedule hourly statistics logging
            schedule.every().hour.do(self._log_stats)
            logger.info("Scheduled hourly statistics logging")
            
            self.running = True
            logger.info("Bot started successfully! Press Ctrl+C to stop.")
            
            # Main loop
            while self.running:
                schedule.run_pending()
                time.sleep(1)
                
            logger.info("Bot stopped.")
            return True
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            return False

    def _post_daily_verse(self, force=False):
        """Scheduled task to post daily verse"""
        try:
            logger.info("Posting daily verse...")
            success = self.daily_poster.post_daily_verse(force=force)
            if success:
                logger.info("Daily verse posted successfully")
            else:
                logger.error("Failed to post daily verse")
        except Exception as e:
            logger.error(f"Error in daily verse posting: {e}")

    def _check_mentions(self):
        """Scheduled task to check and respond to mentions"""
        try:
            logger.info("Checking for mentions...")
            count = self.interaction_handler.process_mentions()
            if count > 0:
                logger.info(f"Processed {count} mentions")
        except Exception as e:
            logger.error(f"Error checking mentions: {e}")

    def _daily_cleanup(self):
        """Scheduled task for daily cleanup"""
        try:
            logger.info("Running daily cleanup...")
            self.interaction_handler.cleanup_old_data(days=30)
            logger.info("Daily cleanup completed")
        except Exception as e:
            logger.error(f"Error in daily cleanup: {e}")

    def _log_stats(self):
        """Scheduled task to log statistics"""
        try:
            stats = self.interaction_handler.get_interaction_stats()
            logger.info(f"Bot Statistics: {stats}")
        except Exception as e:
            logger.error(f"Error logging stats: {e}")

    def run_once(self, task: str = None, force=False):
        """Run a specific task once (for testing/manual execution)"""
        try:
            if not self.twitter_api.verify_credentials():
                logger.error("Failed to verify Twitter credentials")
                return False

            if task == "post_verse" or task is None:
                logger.info("Running daily verse post...")
                return self.daily_poster.post_daily_verse(force=force)
            
            elif task == "check_mentions":
                logger.info("Checking mentions...")
                count = self.interaction_handler.process_mentions()
                logger.info(f"Processed {count} mentions")
                return count > 0
            
            elif task == "stats":
                stats = self.interaction_handler.get_interaction_stats()
                logger.info(f"Bot Statistics: {stats}")
                return True
            
            elif task == "cleanup":
                logger.info("Running cleanup...")
                self.interaction_handler.cleanup_old_data()
                return True
            
            else:
                logger.error(f"Unknown task: {task}")
                return False
                
        except Exception as e:
            logger.error(f"Error running task {task}: {e}")
            return False

    def get_status(self):
        """Get current bot status"""
        try:
            stats = self.interaction_handler.get_interaction_stats()
            posting_history = self.daily_poster.get_posting_history(7)
            
            status = {
                'running': self.running,
                'stats': stats,
                'recent_posts': posting_history,
                'next_scheduled_post': schedule.next_run(),
                'api_status': self.twitter_api.verify_credentials()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {'error': str(e)}

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Check for flags
        dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
        force = "--force" in sys.argv or "-f" in sys.argv
        
        # Remove flags from args for task parsing
        args = [arg for arg in sys.argv[1:] if arg not in ["--dry-run", "-d", "--force", "-f"]]
        
        if not args:
            task = "start"
        else:
            task = args[0].lower()
        
        if task == "help":
            print("""
InChrist AI Bot Commands:
  start          - Start the bot with scheduled tasks
  post_verse     - Post today's verse once
  check_mentions - Check and respond to mentions once
  stats          - Show bot statistics
  cleanup        - Run database cleanup
  status         - Show bot status
  help           - Show this help message
  
Flags:
  --dry-run, -d  - Run in dry run mode (no actual posting to Twitter)
  --force, -f    - Force posting even if already posted today
  
Examples:
  python main.py start --dry-run       # Start in dry run mode
  python main.py post_verse -d         # Test posting without actually posting
  python main.py post_verse --force    # Force post even if already posted today
  python main.py post_verse -d -f      # Dry run force (test multiple times)
  python main.py check_mentions --dry-run  # Test mention handling
            """)
            return
        
        elif task == "start":
            bot = InChristAI(dry_run=dry_run)
            if dry_run:
                logger.info("🏃‍♂️ Starting bot in DRY RUN mode - no actual posting!")
            bot.start()
            
        elif task in ["post_verse", "check_mentions", "stats", "cleanup"]:
            bot = InChristAI(dry_run=dry_run)
            if dry_run and task in ["post_verse", "check_mentions"]:
                logger.info(f"🏃‍♂️ Running '{task}' in DRY RUN mode - no actual posting!")
            if force and task == "post_verse":
                logger.info("🔄 FORCE mode - will post even if already posted today!")
            success = bot.run_once(task, force=force)
            if success:
                print(f"Task '{task}' completed successfully")
            else:
                print(f"Task '{task}' failed")
                
        elif task == "status":
            bot = InChristAI(dry_run=dry_run)
            status = bot.get_status()
            print(f"Bot Status: {status}")
            
        else:
            print(f"Unknown command: {task}")
            print("Use 'python main.py help' for available commands")
    
    else:
        # Default: start the bot
        bot = InChristAI()
        bot.start()

if __name__ == "__main__":
    main()
