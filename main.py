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
            
            # Check actual monthly API usage on startup
            try:
                actual_usage = self.twitter_api.get_actual_usage()
                if 'monthly_used' in actual_usage:
                    monthly_used = actual_usage['monthly_used']
                    monthly_limit = actual_usage.get('monthly_limit', 100)
                    monthly_remaining = actual_usage.get('monthly_remaining', monthly_limit - monthly_used)
                    cap_reset_day = actual_usage.get('cap_reset_day', None)
                    
                    logger.warning(f"📊 ACTUAL MONTHLY API USAGE: {monthly_used}/{monthly_limit} calls used ({actual_usage.get('monthly_percentage', 0):.1f}%), {monthly_remaining} remaining")
                    if cap_reset_day:
                        logger.info(f"📅 Monthly quota resets on day {cap_reset_day} of each month")
                    
                    if monthly_remaining < 20:
                        logger.error(f"⚠️  WARNING: Only {monthly_remaining} API calls remaining this month! Use sparingly.")
                    elif monthly_remaining < 50:
                        logger.warning(f"⚡ CAUTION: {monthly_remaining} API calls remaining this month. Monitor usage carefully.")
                else:
                    logger.info("📊 Could not retrieve actual monthly usage (may need to check manually)")
            except Exception as e:
                logger.warning(f"Could not check actual API usage on startup: {e}")
            
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
            
            # Schedule mention checking once per day (X API Free tier: 100 calls/month limit)
            # This uses ~30 calls/month for mentions (expansions parameter gets original tweet context)
            self._schedule_timezone_aware_task("09:00", bot_timezone, self._check_mentions, "mention checking at 9:00 AM")
            logger.info("Scheduled mention checking once daily at 9:00 AM (X API Free tier: 100 calls/month)")
            
            # Schedule prayer search every 3 days (X API Free tier: 100 calls/month limit)
            # NOTE: Each returned tweet counts as 1 API call, not just the search request
            search_count = getattr(config, 'PRAYER_SEARCH_COUNT', 5)
            search_interval = getattr(config, 'PRAYER_SEARCH_INTERVAL_DAYS', 3)
            
            self._schedule_interval_task("10:00", bot_timezone, search_interval, 
                                        lambda: self._search_and_respond_to_prayers(dry_run=self.dry_run), 
                                        f"prayer search at 10:00 AM (every {search_interval} days)")
            logger.info(f"Scheduled prayer search every {search_interval} days at 10:00 AM ({search_count} tweets per search)")
            
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
            # Step 1: Search for prayer-related tweets
            combined_query = "pray OR \"prayer request\" OR \"thoughts and prayers\""
            search_count = getattr(config, 'PRAYER_SEARCH_COUNT', 5)
            
            tweets = self.twitter_api.search_tweets(combined_query, count=search_count)
            
            if not tweets:
                logger.info("🔍 Prayer search: No tweets found")
                return False
            
            logger.info(f"🔍 Prayer search: Found {len(tweets)} potential tweets")
            for i, tweet in enumerate(tweets, 1):
                logger.info(f"  {i}. {tweet['text'][:80]}...")
            
            # Step 2: Use AI to select best tweet and generate response
            result = self.ai_generator.select_and_respond_to_tweet(tweets)
            
            if not result:
                logger.info("🔍 Prayer search: No suitable tweets found for response")
                return True  # Not an error, just no good candidates
            
            # Step 3: Log the selected tweet and analysis
            logger.info(f"📝 Selected Tweet: {result.selected_tweet.text}")
            logger.info(f"🎯 Detected Mood: {result.detected_mood} - {result.reasoning}")
            logger.info(f"📖 Bible Verse: {result.bible_verse['reference']}")
            
            # Step 4: Check if we've already responded to this tweet
            if self._has_responded_to_tweet_db_only(result.selected_tweet.id):
                logger.info("🔍 Prayer search: Already responded to this tweet, skipping")
                return True
            
            # Step 5: Post the response
            if dry_run:
                logger.info(f"🏃‍♂️ DRY RUN - Would post response: {result.response_text}")
            else:
                reply_id = self.twitter_api.reply_to_tweet(
                    result.selected_tweet.id,
                    result.response_text
                )
                
                if reply_id:
                    logger.info(f"✅ Prayer response posted successfully: {reply_id}")
                    logger.info(f"📝 Response: {result.response_text}")
                    
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
                    except Exception as e:
                        logger.warning(f"Failed to record interaction: {e}")
                else:
                    logger.error("❌ Failed to post prayer response")
                    return False
            
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
            # Temporarily patch the interaction handler to use database-only checks
            # This preserves the search rate limit for prayer search functionality
            original_method = self.interaction_handler._has_responded_to_tweet
            self.interaction_handler._has_responded_to_tweet = lambda tweet_id: self._has_responded_to_tweet_db_only(tweet_id)
            
            try:
                count = self.interaction_handler.process_mentions()
                return count > 0
            finally:
                # Restore original method
                self.interaction_handler._has_responded_to_tweet = original_method
                
        except Exception as e:
            logger.error(f"Error checking mentions: {e}")
            return False

    def _schedule_timezone_aware_task(self, target_time: str, timezone_name: str, task_func, task_description: str = "task"):
        """Schedule a task at a specific time in a specific timezone
        
        Args:
            target_time: Time in HH:MM format (e.g., "09:00")
            timezone_name: Timezone name (e.g., "America/New_York")
            task_func: Function to call when scheduled
            task_description: Description for logging
        """
        try:
            # Create timezone object
            tz = pytz.timezone(timezone_name)
            
            # Parse target time
            hour, minute = map(int, target_time.split(':'))
            
            # Create a wrapper function that handles timezone conversion
            def timezone_aware_task():
                # Execute the task
                task_func()
            
            # Convert target time to UTC for scheduling
            # Create a sample date in the target timezone
            sample_date = datetime.now(tz).replace(hour=hour, minute=minute, second=0, microsecond=0)
            utc_time = sample_date.astimezone(pytz.UTC)
            utc_target_time = utc_time.strftime('%H:%M')
            
            logger.info(f"Converting {target_time} {timezone_name} to {utc_target_time} UTC for {task_description}")
            
            # Schedule using UTC time (what the server runs on)
            schedule.every().day.at(utc_target_time).do(timezone_aware_task)
            
        except Exception as e:
            logger.error(f"Error setting up timezone-aware schedule for {task_description}: {e}")
            # Fallback to regular scheduling
            logger.info(f"Falling back to regular scheduling (UTC) for {task_description}")
            schedule.every().day.at(target_time).do(task_func)

    def _schedule_interval_task(self, target_time: str, timezone_name: str, interval_days: int, task_func, task_description: str = "task"):
        """Schedule a task to run every N days at a specific time in a specific timezone
        
        Args:
            target_time: Time in HH:MM format (e.g., "10:00")
            timezone_name: Timezone name (e.g., "America/New_York")
            interval_days: Number of days between runs (1 = daily, 2 = every other day, 3 = every 3 days, etc.)
            task_func: Function to call when scheduled
            task_description: Description for logging
        """
        try:
            # Create timezone object
            tz = pytz.timezone(timezone_name)
            
            # Parse target time
            hour, minute = map(int, target_time.split(':'))
            
            # Track last run date (simple in-memory tracking)
            last_run_date = [None]  # Use list to allow modification in nested function
            
            # Create a wrapper function that checks interval and handles timezone conversion
            def interval_task():
                # Get current time in target timezone
                current_time_tz = datetime.now(tz)
                current_date = current_time_tz.date()
                current_hour = current_time_tz.hour
                current_minute = current_time_tz.minute
                
                # Only check at the target time (within the target hour)
                if current_hour != hour:
                    return  # Not the right hour yet
                
                # Check if we should run based on interval
                if last_run_date[0] is not None:
                    days_since_last_run = (current_date - last_run_date[0]).days
                    if days_since_last_run < interval_days:
                        return  # Not enough days have passed
                
                # Run if we're at or past the target time
                if current_minute >= minute:
                    logger.info(f"{task_description}: Running (every {interval_days} days)")
                    task_func()
                    last_run_date[0] = current_date
            
            # Schedule to run every hour to check if it's time
            schedule.every().hour.do(interval_task)
            
            logger.info(f"Scheduled {task_description} to run every {interval_days} days at {target_time} {timezone_name}")
            
        except Exception as e:
            logger.error(f"Error setting up interval schedule for {task_description}: {e}")
            # Fallback: schedule daily
            logger.info(f"Falling back to daily scheduling for {task_description}")
            self._schedule_timezone_aware_task(target_time, timezone_name, task_func, task_description)

    def _setup_timezone_aware_schedule(self, posting_time: str, timezone_name: str):
        """Set up timezone-aware daily posting schedule"""
        self._schedule_timezone_aware_task(posting_time, timezone_name, self._post_daily_verse, "Daily post")

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

    def get_status(self, check_actual_usage=False):
        """Get current bot status
        
        Args:
            check_actual_usage: If True, queries X API for actual monthly usage (may count as a read call)
        """
        try:
            stats = self.interaction_handler.get_interaction_stats()
            posting_history = self.daily_poster.get_posting_history(7)
            api_usage_session = self.twitter_api.get_read_call_count()
            
            status = {
                'running': self.running,
                'stats': stats,
                'recent_posts': posting_history,
                'next_scheduled_post': schedule.next_run(),
                'api_status': self.twitter_api.verify_credentials(),
                'api_usage': {
                    'session': api_usage_session,
                }
            }
            
            # Optionally check actual usage (may count as a read call)
            if check_actual_usage:
                try:
                    api_usage_actual = self.twitter_api.get_actual_usage()
                    status['api_usage']['actual_monthly'] = api_usage_actual
                    logger.info("Actual monthly usage retrieved (note: this may count as a read call)")
                except Exception as e:
                    logger.warning(f"Could not retrieve actual usage: {e}")
                    status['api_usage']['actual_monthly'] = {'error': str(e), 'note': 'Could not retrieve'}
            
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
            # Only check actual usage if explicitly requested to save API calls
            check_actual = "--check-usage" in sys.argv or "-u" in sys.argv
            status = bot.get_status(check_actual_usage=check_actual)
            print(f"Bot Status: {status}")
            if not check_actual:
                print("\n💡 Tip: Use --check-usage or -u flag to see actual monthly API usage")
                print("   Note: This may count as a read call")
            
        else:
            print(f"Unknown command: {task}")
            print("Use 'python main.py help' for available commands")
    
    else:
        # Default: start the bot
        bot = InChristAI()
        bot.start()

if __name__ == "__main__":
    main()
