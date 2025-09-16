"""
Handles Twitter interactions, mentions, and responses
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import sqlite3
import os

from twitter_api import TwitterAPI
from ai_responses import AIResponseGenerator
from bible_api import BibleAPI

logger = logging.getLogger(__name__)

class InteractionHandler:
    def __init__(self, dry_run=False):
        self.twitter_api = TwitterAPI(dry_run=dry_run)
        self.ai_generator = AIResponseGenerator()
        self.bible_api = BibleAPI()
        self.dry_run = dry_run
        
        # Initialize database for tracking interactions
        self.db_path = "inchrist_ai.db"
        self._init_database()
        
        # Rate limiting and spam prevention
        self.last_mention_id = None
        self.response_cooldown = 60  # Minimum seconds between responses to same user
        self.max_responses_per_hour = 30
        self.blocked_words = ['spam', 'bot', 'fake', 'scam']
        
    def _init_database(self):
        """Initialize SQLite database for tracking interactions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table for tracking mentions and responses
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT UNIQUE,
                    user_id TEXT,
                    username TEXT,
                    mention_text TEXT,
                    response_text TEXT,
                    response_tweet_id TEXT,
                    created_at TIMESTAMP,
                    responded_at TIMESTAMP,
                    interaction_type TEXT,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            
            # Table for tracking daily posts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE,
                    verse_reference TEXT,
                    verse_text TEXT,
                    tweet_id TEXT,
                    posted_at TIMESTAMP
                )
            ''')
            
            # Table for user preferences and history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    last_interaction TIMESTAMP,
                    interaction_count INTEGER DEFAULT 0,
                    preferred_version TEXT DEFAULT 'ESV',
                    is_blocked BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def process_mentions(self) -> int:
        """Process new mentions and generate responses"""
        try:
            # Get recent mentions from last 24 hours (without since_id to see all recent activity)
            all_mentions = self.twitter_api.get_mentions(since_id=None, count=10)
            
            if not all_mentions:
                logger.info("No mentions found in recent history")
                return 0
            
            # Log all mentions found for visibility
            logger.info(f"Found {len(all_mentions)} mentions in recent history:")
            for i, mention in enumerate(all_mentions, 1):
                status = "NEW" if not self.last_mention_id or mention['id'] > self.last_mention_id else "OLD"
                logger.info(f"  {i}. [{status}] {mention['text'][:50]}... (ID: {mention['id']}, Author: {mention['author_id']})")
            
            # Filter to only new mentions for processing
            new_mentions = []
            if self.last_mention_id:
                new_mentions = [m for m in all_mentions if m['id'] > self.last_mention_id]
            else:
                # If no last_mention_id, treat all as new
                new_mentions = all_mentions
            
            if not new_mentions:
                logger.info("No new mentions to process (all are already handled)")
                return 0
            
            logger.info(f"Processing {len(new_mentions)} new mentions...")
            processed_count = 0
            
            for mention in new_mentions:
                try:
                    # Update last mention ID
                    if not self.last_mention_id or mention['id'] > self.last_mention_id:
                        self.last_mention_id = mention['id']
                    
                    # Check if we should respond to this mention
                    if self._should_respond_to_mention(mention):
                        success = self._process_single_mention(mention)
                        if success:
                            processed_count += 1
                    
                    # Rate limiting - small delay between processing mentions
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing mention {mention['id']}: {e}")
                    continue
            
            logger.info(f"Processed {processed_count} mentions")
            return processed_count
            
        except Exception as e:
            logger.error(f"Failed to process mentions: {e}")
            return 0

    def _should_respond_to_mention(self, mention: Dict) -> bool:
        """Determine if we should respond to a mention"""
        try:
            # Don't respond to our own tweets (check using our known user ID)
            if mention['author_id'] == self.twitter_api.user_id:
                logger.info(f"Skipping mention from ourselves: {mention['id']}")
                return False
            
            # Check if already responded
            if self._has_responded_to_tweet(mention['id']):
                logger.info(f"Already responded to tweet: {mention['id']}")
                return False
            
            # Check for blocked words
            mention_text = mention['text'].lower()
            if any(word in mention_text for word in self.blocked_words):
                logger.info(f"Blocked mention due to spam words: {mention['id']}")
                return False
            
            # Check user rate limiting
            if self._is_user_rate_limited(mention['author_id']):
                logger.info(f"User is rate limited: {mention['author_id']}")
                return False
            
            # Check hourly response limit
            if self._hourly_response_limit_reached():
                logger.info(f"Hourly response limit reached")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if should respond to mention: {e}")
            return False

    def _process_single_mention(self, mention: Dict) -> bool:
        """Process a single mention and generate response"""
        try:
            # Create minimal user info from mention data (no API call needed)
            user_info = {
                'id': mention['author_id'],
                'username': 'TwitterUser',  # Generic, since we don't need real username for replies
                'name': 'Twitter User'
            }
            
            # Store interaction in database
            self._store_interaction(mention, user_info)
            
            # Generate AI response (no username needed - Twitter handles reply tagging automatically)
            response_text = self.ai_generator.generate_response(
                mention_text=mention['text'],
                user_info=user_info,
                context=f"Someone on Twitter is asking for spiritual guidance"
            )
            
            if not response_text:
                logger.error(f"Failed to generate response for mention {mention['id']}")
                return False
            
            # Post reply
            reply_tweet_id = self.twitter_api.reply_to_tweet(mention['id'], response_text)
            
            if reply_tweet_id:
                # Update database with response
                self._update_interaction_response(mention['id'], response_text, reply_tweet_id)
                logger.info(f"Successfully responded to mention {mention['id']}")
                return True
            else:
                logger.error(f"Failed to post reply to mention {mention['id']}")
                return False
            
        except Exception as e:
            logger.error(f"Error processing single mention: {e}")
            return False

    def _store_interaction(self, mention: Dict, user_info: Dict = None):
        """Store interaction in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO interactions 
                (tweet_id, user_id, username, mention_text, created_at, interaction_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                mention['id'],
                mention['author_id'],
                user_info['username'] if user_info else None,
                mention['text'],
                mention['created_at'],
                'mention'
            ))
            
            # Update user information
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, last_interaction, interaction_count)
                VALUES (?, ?, ?, COALESCE((SELECT interaction_count FROM users WHERE user_id = ?) + 1, 1))
            ''', (
                mention['author_id'],
                user_info['username'] if user_info else None,
                datetime.now(),
                mention['author_id']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing interaction: {e}")

    def _update_interaction_response(self, mention_id: str, response_text: str, reply_tweet_id: str):
        """Update interaction with response information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE interactions 
                SET response_text = ?, response_tweet_id = ?, responded_at = ?, status = 'completed'
                WHERE tweet_id = ?
            ''', (response_text, reply_tweet_id, datetime.now(), mention_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating interaction response: {e}")

    def _has_responded_to_tweet(self, tweet_id: str) -> bool:
        """Check if we've already responded to a tweet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT response_tweet_id FROM interactions WHERE tweet_id = ?', (tweet_id,))
            result = cursor.fetchone()
            
            conn.close()
            return result is not None and result[0] is not None
            
        except Exception as e:
            logger.error(f"Error checking if responded to tweet: {e}")
            return False

    def _is_user_rate_limited(self, user_id: str) -> bool:
        """Check if user is rate limited"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check last interaction time
            cursor.execute('SELECT last_interaction FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            if result:
                last_interaction = datetime.fromisoformat(result[0])
                time_diff = (datetime.now() - last_interaction).total_seconds()
                
                if time_diff < self.response_cooldown:
                    logger.info(f"User {user_id} is rate limited")
                    return True
            
            conn.close()
            return False
            
        except Exception as e:
            logger.error(f"Error checking user rate limit: {e}")
            return False

    def _hourly_response_limit_reached(self) -> bool:
        """Check if hourly response limit is reached"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            one_hour_ago = datetime.now() - timedelta(hours=1)
            cursor.execute(
                'SELECT COUNT(*) FROM interactions WHERE responded_at > ? AND status = "completed"',
                (one_hour_ago,)
            )
            
            count = cursor.fetchone()[0]
            conn.close()
            
            if count >= self.max_responses_per_hour:
                logger.warning(f"Hourly response limit reached: {count}/{self.max_responses_per_hour}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking hourly limit: {e}")
            return False

    def get_interaction_stats(self) -> Dict:
        """Get statistics about interactions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total interactions
            cursor.execute('SELECT COUNT(*) FROM interactions')
            total_interactions = cursor.fetchone()[0]
            
            # Successful responses
            cursor.execute('SELECT COUNT(*) FROM interactions WHERE status = "completed"')
            successful_responses = cursor.fetchone()[0]
            
            # Today's activity
            today = datetime.now().date()
            cursor.execute('SELECT COUNT(*) FROM interactions WHERE DATE(created_at) = ?', (today,))
            today_interactions = cursor.fetchone()[0]
            
            # Unique users
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM interactions')
            unique_users = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_interactions': total_interactions,
                'successful_responses': successful_responses,
                'today_interactions': today_interactions,
                'unique_users': unique_users,
                'response_rate': (successful_responses / total_interactions * 100) if total_interactions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting interaction stats: {e}")
            return {}

    def cleanup_old_data(self, days: int = 30):
        """Clean up old interaction data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('DELETE FROM interactions WHERE created_at < ?', (cutoff_date,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} old interactions")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
