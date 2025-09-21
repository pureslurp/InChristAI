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
from typing import Dict, List
import pytz

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
from ai_responses import AIResponseGenerator

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
        self.ai_generator = AIResponseGenerator()
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
            
            # Get timezone for scheduling
            bot_timezone = getattr(config, 'TIMEZONE', 'America/New_York')
            logger.info(f"Using timezone: {bot_timezone}")
            
            # Create timezone-aware scheduler
            self._setup_timezone_aware_schedule(posting_time, bot_timezone)
            logger.info(f"Scheduled daily verse posting at {posting_time} {bot_timezone}")
            
            # Startup mentions check removed - will check on schedule only
            logger.info("Skipping startup mention check - will begin checking on schedule")
            
            # Schedule mention checking every hour (conservative API usage)
            schedule.every().hour.do(self._check_mentions)
            logger.info("Scheduled mention checking every hour (conservative API usage)")
            
            # Schedule prayer search and response every 4 hours (dry-run mode)
            schedule.every(4).hours.do(lambda: self._search_and_respond_to_prayers(dry_run=True))
            logger.info("Scheduled prayer search and response every 4 hours (dry-run mode)")
            
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
    
    def _search_and_respond_to_prayers(self, dry_run=False):
        """Scheduled task to search for prayer requests and respond with encouragement"""
        try:
            logger.info("🙏 Starting prayer search and response cycle...")
            
            # Step 1: Search for prayer-related tweets (SINGLE Twitter API call)
            # Use OR operator to search for multiple terms in one request
            combined_query = "pray OR \"prayer request\" OR \"thoughts and prayers\""
            logger.info(f"Making single Twitter API call with query: {combined_query}")
            
            tweets = self.twitter_api.search_tweets(combined_query, count=50)  # Increased count for better variety
            
            if not tweets:
                logger.warning("No tweets found - likely rate limited or no matching content")
                return False
            
            logger.info(f"✅ Found {len(tweets)} prayer-related tweets with 1 API call")
            
            # Step 2: Use AI to select best tweet and generate response
            result = self.ai_generator.select_and_respond_to_tweet(tweets)
            
            if not result:
                logger.info("AI found no suitable tweets for spiritual response")
                return True  # Not an error, just no good candidates
            
            # Step 3: Log the analysis results
            logger.info("🎯 AI Analysis Results:")
            logger.info(f"Selected Tweet (FULL): {result.selected_tweet.text}")
            logger.info(f"Author: {result.selected_tweet.author_id}")
            logger.info(f"Tweet ID: {result.selected_tweet.id}")
            logger.info(f"Detected Mood: {result.detected_mood}")
            logger.info(f"Bible Verse: {result.bible_verse['reference']}")
            logger.info(f"Response Length: {len(result.response_text)} chars")
            
            # Step 4: Check if we've already responded to this tweet (database only to avoid extra API calls)
            if self._has_responded_to_tweet_db_only(result.selected_tweet.id):
                logger.info("Already responded to this tweet, skipping...")
                return True
            
            # Step 5: Post the response
            if dry_run:
                logger.info("🏃‍♂️ DRY RUN - Would post prayer response:")
                logger.info(f"Tweet ID: {result.selected_tweet.id}")
                logger.info(f"Response: {result.response_text}")
            else:
                logger.info("📤 Posting prayer response...")
                reply_id = self.twitter_api.reply_to_tweet(
                    result.selected_tweet.id,
                    result.response_text
                )
                
                if reply_id:
                    logger.info(f"✅ Successfully posted prayer response: {reply_id}")
                    
                    # Record the interaction in database
                    try:
                        self.interaction_handler._record_interaction(
                            result.selected_tweet.id,
                            result.selected_tweet.author_id,
                            result.selected_tweet.text,
                            result.response_text,
                            reply_id,
                            'prayer_response'
                        )
                        logger.info("Interaction recorded in database")
                    except Exception as e:
                        logger.warning(f"Failed to record interaction: {e}")
                        
                else:
                    logger.error("❌ Failed to post prayer response")
                    return False
            
            logger.info("🙏 Prayer search and response cycle completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in prayer search and response: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _has_responded_to_tweet_db_only(self, tweet_id: str) -> bool:
        """Check if we've responded to a tweet using only database (no API calls)"""
        try:
            results = self.interaction_handler.db.execute_query(
                'SELECT response_tweet_id FROM interactions WHERE tweet_id = %s' if self.interaction_handler.db.is_postgres else 
                'SELECT response_tweet_id FROM interactions WHERE tweet_id = ?', 
                (tweet_id,)
            )
            
            if results and results[0]['response_tweet_id'] is not None:
                logger.info(f"Database shows we responded to {tweet_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Database check failed for tweet {tweet_id}: {e}")
            return False  # Assume we haven't responded if database fails

    def _check_mentions(self):
        """Scheduled task to check and respond to mentions (database-only to preserve rate limits)"""
        try:
            logger.info("🔔 Checking mentions...")
            # Temporarily patch the interaction handler to use database-only checks
            # This preserves the search rate limit for prayer search functionality
            original_method = self.interaction_handler._has_responded_to_tweet
            self.interaction_handler._has_responded_to_tweet = lambda tweet_id: self._has_responded_to_tweet_db_only(tweet_id)
            
            try:
                count = self.interaction_handler.process_mentions()
                logger.info(f"✅ Processed {count} mentions (database-only checks)")
                return count > 0
            finally:
                # Restore original method
                self.interaction_handler._has_responded_to_tweet = original_method
                
        except Exception as e:
            logger.error(f"Error checking mentions: {e}")
            return False

    def _setup_timezone_aware_schedule(self, posting_time: str, timezone_name: str):
        """Set up timezone-aware daily posting schedule"""
        try:
            # Create timezone object
            tz = pytz.timezone(timezone_name)
            
            # Get current time in the target timezone
            now_tz = datetime.now(tz)
            logger.info(f"Current time in {timezone_name}: {now_tz.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Parse posting time
            hour, minute = map(int, posting_time.split(':'))
            
            # Create a wrapper function that handles timezone conversion
            def timezone_aware_post():
                # Get current time in target timezone
                current_time_tz = datetime.now(tz)
                logger.info(f"Daily post check: Current time in {timezone_name}: {current_time_tz.strftime('%H:%M:%S')}, Target: {posting_time}")
                
                # For schedule library, we need to let it handle the daily scheduling
                # Just execute the post since schedule already determined it's time
                self._post_daily_verse()
            
            # Convert target time to UTC for scheduling
            # Create a sample date in the target timezone
            sample_date = datetime.now(tz).replace(hour=hour, minute=minute, second=0, microsecond=0)
            utc_time = sample_date.astimezone(pytz.UTC)
            utc_posting_time = utc_time.strftime('%H:%M')
            
            logger.info(f"Converting {posting_time} {timezone_name} to {utc_posting_time} UTC for scheduling")
            
            # Schedule using UTC time (what the server runs on)
            schedule.every().day.at(utc_posting_time).do(timezone_aware_post)
            
        except Exception as e:
            logger.error(f"Error setting up timezone-aware schedule: {e}")
            # Fallback to regular scheduling
            logger.info("Falling back to regular scheduling (UTC)")
            schedule.every().day.at(posting_time).do(self._post_daily_verse)

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
            
            elif task == "test_prayer_search":
                logger.info("Prayer search tests have been moved to test_prayer_bot.py")
                logger.info("Run: python test_prayer_bot.py workflow --help for options")
                return True
                
            elif task == "prayer_search":
                logger.info("Running prayer search and response...")
                return self._search_and_respond_to_prayers()
            
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
  start              - Start the bot with scheduled tasks
  post_verse         - Post today's verse once
  check_mentions     - Check and respond to mentions once
  prayer_search      - Search for prayer requests and respond once
  stats              - Show bot statistics
  cleanup            - Run database cleanup
  status             - Show bot status
  help               - Show this help message
  
Flags:
  --dry-run, -d  - Run in dry run mode (no actual posting to Twitter)
  --force, -f    - Force posting even if already posted today
  
Examples:
  python main.py start --dry-run               # Start in dry run mode
  python main.py post_verse -d                 # Test posting without actually posting
  python main.py post_verse --force            # Force post even if already posted today
  python main.py post_verse -d -f              # Dry run force (test multiple times)
  python main.py check_mentions --dry-run      # Test mention handling
  python main.py prayer_search --dry-run       # Test prayer search and response
  python test_prayer_bot.py workflow --help   # Advanced prayer search testing
            """)
            return
        
        elif task == "start":
            bot = InChristAI(dry_run=dry_run)
            if dry_run:
                logger.info("🏃‍♂️ Starting bot in DRY RUN mode - no actual posting!")
            bot.start()
            
        elif task in ["post_verse", "check_mentions", "stats", "cleanup", "test_prayer_search", "prayer_search"]:
            bot = InChristAI(dry_run=dry_run)
            if dry_run and task in ["post_verse", "check_mentions", "prayer_search"]:
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
