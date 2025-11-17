"""
Handles Twitter interactions, mentions, and responses
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os

from twitter_api import TwitterAPI
from ai_responses import AIResponseGenerator
from bible_api import BibleAPI
from database import DatabaseManager

logger = logging.getLogger(__name__)

class InteractionHandler:
    def __init__(self, dry_run=False):
        self.twitter_api = TwitterAPI(dry_run=dry_run)
        self.ai_generator = AIResponseGenerator()
        self.bible_api = BibleAPI()
        self.dry_run = dry_run
        
        # Initialize database manager (PostgreSQL on Railway)
        self.db = DatabaseManager()
        self.db.init_tables()
        
        # Rate limiting and spam prevention
        self.last_mention_id = None
        self.response_cooldown = 60  # Minimum seconds between responses to same user
        self.max_responses_per_hour = 30
        self.blocked_words = ['spam', 'bot', 'fake', 'scam']
        

    def process_mentions(self) -> int:
        """Process new mentions and generate responses"""
        try:
            # Get recent mentions - maximize data retrieval for our precious daily API call
            # Use max count and get all mentions since last check (X API Free tier: 100 calls/month)
            all_mentions = self.twitter_api.get_mentions(since_id=None, count=25)
            
            if not all_mentions:
                logger.info("No mentions found in recent history")
                return 0
            
            
            # Log all mentions found for visibility
            logger.info(f"Found {len(all_mentions)} mentions in recent history:")
            for i, mention in enumerate(all_mentions, 1):
                status = "NEW" if not self.last_mention_id or mention['id'] > self.last_mention_id else "OLD"
                logger.info(f"  {i}. [{status}] {mention['text'][:50]}... (ID: {mention['id']}, Author: {mention['author_id']})")
            
            # Filter to only unprocessed mentions (check database for each)
            unprocessed_mentions = []
            for mention in all_mentions:
                logger.info(f"🔍 Checking if we've responded to mention ID: {mention['id']}")
                has_responded = self._has_responded_to_tweet(mention['id'])
                logger.info(f"📊 _has_responded_to_tweet returned: {has_responded}")
                if not has_responded:
                    unprocessed_mentions.append(mention)
                else:
                    logger.info(f"Skipping already processed mention: {mention['id']}")
            
            if not unprocessed_mentions:
                logger.info("No unprocessed mentions found (all have been responded to)")
                return 0
            
            logger.info(f"Processing {len(unprocessed_mentions)} unprocessed mentions...")
            processed_count = 0
            
            for mention in unprocessed_mentions:
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
            
            # Get original tweet context if this mention is a reply
            context = self._get_mention_context(mention)
            
            # Generate AI response (no username needed - Twitter handles reply tagging automatically)
            response_text = self.ai_generator.generate_response(
                mention_text=mention['text'],
                user_info=user_info,
                context=context
            )
            
            if not response_text:
                logger.error(f"Failed to generate response for mention {mention['id']}")
                return False
            
            # Check if AI decided not to reply
            if response_text.strip().upper() == "NO_REPLY":
                logger.info(f"AI decided not to reply to mention {mention['id']} (combative/inappropriate content)")
                # Still record the interaction but mark as "no response needed"
                self._update_interaction_response(mention['id'], "NO_REPLY", None)
                return True  # This is successful - we appropriately chose not to respond
            
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

    def _get_mention_context(self, mention: Dict) -> str:
        """Get context for a mention, including original tweet if it's a reply"""
        try:
            base_context = "Someone on Twitter is asking for spiritual guidance"
            
            # Check if this mention has original tweet data (already fetched in the same API call)
            original_tweet = mention.get('original_tweet')
            if original_tweet:
                original_text = original_tweet.get('text', '')
                if original_text:
                    # Limit original tweet text to avoid making the context too long
                    max_context_length = 200
                    if len(original_text) > max_context_length:
                        original_text = original_text[:max_context_length] + "..."
                    
                    context_with_original = f"{base_context}. They are replying to this original tweet: \"{original_text}\""
                    logger.info(f"Added original tweet context from mention data: {original_text[:50]}...")
                    return context_with_original
                else:
                    logger.warning(f"Original tweet found but has no text")
            else:
                # Check if this is a reply but we didn't get the original tweet in the API response
                conversation_id = mention.get('conversation_id')
                mention_id = mention.get('id')
                
                # Log reply status - no additional API calls needed
                # The expansions parameter in get_mentions should handle most original tweet context
                if conversation_id and mention_id and str(conversation_id) != str(mention_id):
                    logger.info(f"Mention {mention_id} is a reply but original tweet context not available in API response")
                    logger.info(f"Bot will respond with general context (expansions parameter should handle most cases)")
                else:
                    logger.info(f"Mention {mention_id} is not a reply")
            
            return base_context
            
        except Exception as e:
            logger.error(f"Error getting mention context: {e}")
            return "Someone on Twitter is asking for spiritual guidance"

    def _store_interaction(self, mention: Dict, user_info: Dict = None):
        """Store interaction in database"""
        try:
            # Ensure tweet_id is stored as a string for consistent database queries
            tweet_id = str(mention['id']).strip()
            user_id = str(mention['author_id']).strip()
            
            # Store interaction
            self.db.execute_update('''
                INSERT INTO interactions 
                (tweet_id, user_id, username, mention_text, created_at, interaction_type)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tweet_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    username = EXCLUDED.username,
                    mention_text = EXCLUDED.mention_text,
                    created_at = EXCLUDED.created_at,
                    interaction_type = EXCLUDED.interaction_type
            ''', (
                tweet_id,
                user_id,
                user_info['username'] if user_info else None,
                mention['text'],
                mention['created_at'],
                'mention'
            ))
            
            # Update user information
            self.db.execute_update('''
                INSERT INTO users 
                (user_id, username, last_interaction, interaction_count)
                VALUES (%s, %s, %s, 1)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    last_interaction = EXCLUDED.last_interaction,
                    interaction_count = users.interaction_count + 1
            ''', (
                mention['author_id'],
                user_info['username'] if user_info else None,
                datetime.now()
            ))
            
        except Exception as e:
            logger.error(f"Error storing interaction: {e}")

    def _update_interaction_response(self, mention_id: str, response_text: str, reply_tweet_id: str):
        """Update interaction with response information"""
        try:
            # Ensure tweet_id is a string for consistent database queries
            tweet_id_str = str(mention_id).strip()
            response_id_str = str(reply_tweet_id).strip() if reply_tweet_id else None
            
            logger.info(f"💾 Updating interaction response: tweet_id={tweet_id_str}, response_id={response_id_str}")
            
            self.db.execute_update('''
                UPDATE interactions 
                SET response_text = %s, response_tweet_id = %s, responded_at = %s, status = 'completed'
                WHERE tweet_id = %s
            ''', (response_text, response_id_str, datetime.now(), tweet_id_str))
            
            logger.info(f"✅ Successfully updated interaction response for tweet_id: {tweet_id_str}")
            
        except Exception as e:
            logger.error(f"Error updating interaction response: {e}")

    def _record_interaction(self, tweet_id: str, user_id: str, tweet_text: str, response_text: str, reply_tweet_id: str, interaction_type: str = 'interaction'):
        """Record a complete interaction (tweet and reply) in the database
        
        This method stores both the original tweet ID and the reply tweet ID,
        ensuring we have a complete record without needing additional API calls.
        
        Args:
            tweet_id: The ID of the original tweet we responded to
            user_id: The ID of the user who created the original tweet
            tweet_text: The text of the original tweet
            response_text: The text of our reply
            reply_tweet_id: The ID of our reply tweet
            interaction_type: Type of interaction (e.g., 'mention', 'prayer_response')
        """
        try:
            # Ensure IDs are stored as strings for consistent database queries
            tweet_id_str = str(tweet_id).strip()
            user_id_str = str(user_id).strip()
            reply_tweet_id_str = str(reply_tweet_id).strip() if reply_tweet_id else None
            
            logger.info(f"💾 Recording interaction: tweet_id={tweet_id_str}, reply_id={reply_tweet_id_str}, type={interaction_type}")
            
            # Insert or update interaction with all information in one operation
            self.db.execute_update('''
                INSERT INTO interactions 
                (tweet_id, user_id, mention_text, response_text, response_tweet_id, 
                 created_at, responded_at, interaction_type, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tweet_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    mention_text = EXCLUDED.mention_text,
                    response_text = EXCLUDED.response_text,
                    response_tweet_id = EXCLUDED.response_tweet_id,
                    responded_at = EXCLUDED.responded_at,
                    interaction_type = EXCLUDED.interaction_type,
                    status = 'completed'
            ''', (
                tweet_id_str,
                user_id_str,
                tweet_text,
                response_text,
                reply_tweet_id_str,
                datetime.now(),  # created_at
                datetime.now(),  # responded_at
                interaction_type,
                'completed'
            ))
            
            # Also update user information
            self.db.execute_update('''
                INSERT INTO users 
                (user_id, last_interaction, interaction_count)
                VALUES (%s, %s, 1)
                ON CONFLICT (user_id) DO UPDATE SET
                    last_interaction = EXCLUDED.last_interaction,
                    interaction_count = users.interaction_count + 1
            ''', (user_id_str, datetime.now()))
            
            logger.info(f"✅ Recorded interaction: tweet_id={tweet_id_str}, reply_id={reply_tweet_id_str}, type={interaction_type}")
            
        except Exception as e:
            logger.error(f"Error recording interaction: {e}")
            raise  # Re-raise to ensure caller knows if recording failed

    def _has_responded_to_tweet(self, tweet_id: str) -> bool:
        """Check if we've already responded to a tweet (database only to preserve API quota)
        
        WARNING: Do NOT add Twitter API verification here - it causes expensive API calls
        that quickly exhaust the monthly quota. The database is the source of truth.
        """
        try:
            logger.info(f"🚀 _has_responded_to_tweet called with tweet_id: {tweet_id} (type: {type(tweet_id).__name__})")
            logger.info(f"💾 Database type: PostgreSQL, URL: {self.db.database_url[:50]}...")
            
            # CRITICAL: Verify we're using PostgreSQL, not SQLite
            if not self.db.is_postgres:
                logger.error(f"❌ CRITICAL ERROR: Database is not PostgreSQL! Type: {type(self.db).__name__}, URL: {self.db.database_url}")
                logger.error(f"   This will cause incorrect query results. Expected PostgreSQL but got: {self.db.database_url}")
                # Still try to query, but log the error
            
            # Debug: Show recent tweet_ids in database for comparison
            try:
                debug_query = 'SELECT tweet_id, response_tweet_id, status FROM interactions ORDER BY created_at DESC LIMIT 5'
                debug_results = self.db.execute_query(debug_query)
                if debug_results:
                    existing_ids = []
                    for r in debug_results:
                        db_tweet_id = str(r.get('tweet_id', ''))
                        db_response_id = r.get('response_tweet_id')
                        db_status = r.get('status', 'unknown')
                        existing_ids.append(f"{db_tweet_id} (response: {db_response_id}, status: {db_status})")
                    logger.info(f"🔍 Recent tweet_ids in database: {existing_ids}")
                    # Also show raw values for comparison
                    raw_ids = [str(r.get('tweet_id', '')) for r in debug_results]
                    logger.info(f"🔍 Raw tweet_id values: {[repr(id) for id in raw_ids]}")
                else:
                    logger.warning(f"⚠️  No interactions found in database!")
            except Exception as debug_err:
                logger.warning(f"⚠️  Could not fetch debug info: {debug_err}")
            
            # Ensure tweet_id is a string for consistent database comparison
            tweet_id_str = str(tweet_id).strip()
            
            # Log the exact value we're searching for (helpful for debugging)
            logger.info(f"🔎 Searching for tweet_id: '{tweet_id_str}' (length: {len(tweet_id_str)}, repr: {repr(tweet_id_str)})")
            
            # Check our database only - no API calls to preserve quota
            query = 'SELECT response_tweet_id, status FROM interactions WHERE tweet_id = %s'
            logger.info(f"🔍 Checking database for tweet_id: '{tweet_id_str}' (type: {type(tweet_id_str).__name__})")
            logger.info(f"📝 Query: {query}")
            
            try:
                results = self.db.execute_query(query, (tweet_id_str,))
                logger.info(f"📊 Database query returned {len(results) if results else 0} result(s)")
            except Exception as query_error:
                logger.error(f"❌ Database query failed: {query_error}")
                import traceback
                logger.error(f"Query error traceback: {traceback.format_exc()}")
                raise  # Re-raise to be caught by outer try/except
            
            if results and len(results) > 0:
                result = results[0]
                response_tweet_id = result.get('response_tweet_id')
                status = result.get('status', 'unknown')
                
                logger.info(f"📋 Database record found: response_tweet_id={response_tweet_id}, status={status}")
                
                # Check if we have a response tweet ID (not NULL)
                if response_tweet_id is not None and str(response_tweet_id).strip():
                    logger.info(f"✅ Database shows we responded to {tweet_id_str} (response_id: {response_tweet_id})")
                    return True
                else:
                    logger.warning(f"⚠️  Database record exists but response_tweet_id is NULL/empty for {tweet_id_str} (status: {status})")
                    logger.warning(f"   This might mean the reply failed or was marked as NO_REPLY")
                    return False
            else:
                # No record found in database
                logger.info(f"❌ No database record found for tweet_id: {tweet_id_str}")
                logger.info(f"   This means we haven't responded to this tweet yet")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error checking if responded to tweet {tweet_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # If database fails, err on side of caution - assume not replied (but don't make API call)
            return False

    def _is_user_rate_limited(self, user_id: str) -> bool:
        """Check if user is rate limited"""
        try:
            # Check last interaction time
            results = self.db.execute_query(
                'SELECT last_interaction FROM users WHERE user_id = %s', 
                (user_id,)
            )
            
            if results:
                last_interaction = datetime.fromisoformat(results[0]['last_interaction'])
                time_diff = (datetime.now() - last_interaction).total_seconds()
                
                if time_diff < self.response_cooldown:
                    logger.info(f"User {user_id} is rate limited")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking user rate limit: {e}")
            return False

    def _hourly_response_limit_reached(self) -> bool:
        """Check if hourly response limit is reached"""
        try:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            results = self.db.execute_query(
                'SELECT COUNT(*) as count FROM interactions WHERE responded_at > %s AND status = %s',
                (one_hour_ago, 'completed')
            )
            
            count = results[0]['count']
            
            if count >= self.max_responses_per_hour:
                logger.warning(f"Hourly response limit reached: {count}/{self.max_responses_per_hour}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking hourly limit: {e}")
            return False

    def get_interaction_stats(self) -> Dict:
        """Get statistics about interactions"""
        return self.db.get_stats()

    def cleanup_old_data(self, days: int = 30):
        """Clean up old interaction data"""
        return self.db.cleanup_old_data(days)
