"""
Daily Bible verse posting functionality
"""
import logging
from datetime import datetime, date
from typing import Dict, Optional
import random

from twitter_api import TwitterAPI
from bible_api import BibleAPI, get_fallback_verse
from ai_responses import AIResponseGenerator
from database import DatabaseManager

logger = logging.getLogger(__name__)

class DailyPoster:
    def __init__(self, dry_run=False):
        self.twitter_api = TwitterAPI(dry_run=dry_run)
        self.bible_api = BibleAPI()
        self.ai_generator = AIResponseGenerator()
        self.db = DatabaseManager()
        self.dry_run = dry_run
        
        # Posting approach: verse first, then reply with reflection
        self.use_two_tweet_format = True
        
    def post_daily_verse(self, force=False) -> bool:
        """Post the daily Bible verse"""
        try:
            today = date.today()
            
            # Check if we've already posted today (unless forced)
            if not force and self._has_posted_today(today):
                logger.info("Daily verse already posted today")
                return True
            
            # Get a verse for today
            verse_data = self._get_todays_verse()
            if not verse_data:
                logger.error("Failed to get verse for today")
                return False
            
            if self.use_two_tweet_format:
                # Two-tweet format: verse first, then reflection reply
                success = self._post_verse_with_reply(verse_data, today, force)
                return success
            else:
                # Original single tweet format
                tweet_text = self._format_daily_tweet(verse_data)
                tweet_id = self.twitter_api.post_tweet(tweet_text)
                
                if tweet_id:
                    self._record_daily_post(today, verse_data, tweet_id, force=force)
                    logger.info(f"Successfully posted daily verse: {tweet_id}")
                    return True
                else:
                    logger.error("Failed to post daily verse")
                    return False
                
        except Exception as e:
            logger.error(f"Error posting daily verse: {e}")
            return False

    def _get_todays_verse(self) -> Optional[Dict]:
        """Get a verse for today's post"""
        try:
            # Try to get verse from API
            verse_data = self.bible_api.get_daily_verse()
            
            if verse_data:
                return verse_data
            
            # Fallback to preset verses if API fails
            logger.warning("Bible API failed, using fallback verse")
            return get_fallback_verse()
            
        except Exception as e:
            logger.error(f"Error getting today's verse: {e}")
            return get_fallback_verse()

    def _post_verse_with_reply(self, verse_data: Dict, today: date, force: bool = False) -> bool:
        """Post verse first, then reply with AI reflection"""
        try:
            # Format the main verse tweet (clean and simple)
            verse_tweet = self._format_verse_only_tweet(verse_data)
            
            # Post the main verse tweet
            main_tweet_id = self.twitter_api.post_tweet(verse_tweet)
            if not main_tweet_id:
                logger.error("Failed to post main verse tweet")
                return False
            
            logger.info(f"Posted main verse tweet: {main_tweet_id}")
            
            # Generate AI reflection for the reply
            reflection = self.ai_generator.generate_daily_post_text(verse_data)
            
            # Post the reflection as a reply
            reply_tweet_id = self.twitter_api.reply_to_tweet(main_tweet_id, reflection)
            if not reply_tweet_id:
                logger.warning(f"Failed to post reflection reply, but main tweet succeeded: {main_tweet_id}")
                # Still consider this a success since the main tweet posted
            else:
                logger.info(f"Posted reflection reply: {reply_tweet_id}")
            
            # Record in database
            self._record_daily_post(today, verse_data, main_tweet_id, force=force, reply_id=reply_tweet_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in two-tweet posting: {e}")
            return False

    def _format_verse_only_tweet(self, verse_data: Dict) -> str:
        """Format a clean verse-only tweet"""
        reference = verse_data['reference']
        text = verse_data['text']
        version = verse_data['version']
        
        # Simple, clean format with optional hashtags
        tweet_options = [
            f'"{text}"\n\n{reference} ({version})',
            f'"{text}"\n\n{reference} ({version})\n\n#BibleVerse #Faith',
            f'"{text}"\n\n- {reference} ({version})',
        ]
        
        # Choose the option that fits best
        for option in tweet_options:
            if len(option) <= 280:
                return option
        
        # Fallback: truncate verse if needed
        max_text_length = 280 - len(f'"\n\n{reference} ({version})')
        if max_text_length > 50:
            truncated_text = text[:max_text_length-3] + "..."
            return f'"{truncated_text}"\n\n{reference} ({version})'
        
        # Last resort: just reference
        return f'{reference} ({version})'

    def _format_daily_tweet(self, verse_data: Dict, force_style: str = None) -> str:
        """Format the daily verse tweet with variety"""
        try:
            # Choose a random posting style for variety (or use forced style)
            style = force_style or random.choice(self.posting_styles)
            logger.info(f"Formatting daily tweet with style: {style}")
            
            reference = verse_data['reference']
            text = verse_data['text']
            version = verse_data['version']
            
            if style == 'verse_only':
                return self.twitter_api.format_verse_tweet(verse_data)
            
            elif style == 'verse_with_intro':
                intro = self._get_intro_text()
                tweet = f"{intro}\n\n\"{text}\"\n\n{reference} ({version})"
                return self._ensure_tweet_length(tweet)
            
            elif style == 'verse_with_reflection':
                reflection = self.ai_generator.generate_daily_post_text(verse_data)
                
                # Try different formatting options based on length
                option1 = f"{reflection}\n\n\"{text}\"\n\n{reference} ({version})"
                if len(option1) <= 280:
                    return option1
                
                # If too long, try without quotes around verse
                option2 = f"{reflection}\n\n{text}\n\n{reference} ({version})"
                if len(option2) <= 280:
                    return option2
                
                # If still too long, truncate reflection
                max_reflection_length = 280 - len(f"\n\n{text}\n\n{reference} ({version})")
                if max_reflection_length > 20:
                    truncated_reflection = reflection[:max_reflection_length-3] + "..."
                    return f"{truncated_reflection}\n\n{text}\n\n{reference} ({version})"
                
                # Last resort: just verse with reference
                return f"{text}\n\n{reference} ({version})"
            
            elif style == 'verse_with_hashtags':
                hashtags = self._get_relevant_hashtags(text)
                tweet = f"\"{text}\"\n\n{reference} ({version})\n\n{hashtags}"
                return self._ensure_tweet_length(tweet)
            
            elif style == 'verse_with_emojis':
                emoji = self._get_relevant_emoji(text)
                tweet = f"{emoji} \"{text}\"\n\n{reference} ({version}) {emoji}"
                return self._ensure_tweet_length(tweet)
            
            # Default fallback
            return self.twitter_api.format_verse_tweet(verse_data)
            
        except Exception as e:
            logger.error(f"Error formatting daily tweet: {e}")
            return self.twitter_api.format_verse_tweet(verse_data)

    def _get_intro_text(self) -> str:
        """Get a random intro text for the daily verse"""
        intros = [
            "Good morning! Start your day with this truth:",
            "Today's encouragement from God's Word:",
            "Let this verse guide your day:",
            "God's promise for you today:",
            "May this verse bless your heart:",
            "Remember this truth today:",
            "God's Word for your day:",
            "Here's some hope for your day:",
            "Let this encourage you today:",
            "Today's reminder from Scripture:"
        ]
        return random.choice(intros)

    def _get_relevant_hashtags(self, verse_text: str) -> str:
        """Get relevant hashtags based on verse content"""
        text_lower = verse_text.lower()
        
        # Determine themes in the verse
        hashtags = ['#BibleVerse', '#Faith']
        
        if any(word in text_lower for word in ['love', 'beloved', 'heart']):
            hashtags.append('#Love')
        if any(word in text_lower for word in ['peace', 'rest', 'calm']):
            hashtags.append('#Peace')
        if any(word in text_lower for word in ['hope', 'future', 'plans']):
            hashtags.append('#Hope')
        if any(word in text_lower for word in ['strength', 'strong', 'power']):
            hashtags.append('#Strength')
        if any(word in text_lower for word in ['joy', 'rejoice', 'glad']):
            hashtags.append('#Joy')
        if any(word in text_lower for word in ['fear', 'afraid', 'worry']):
            hashtags.append('#NoFear')
        if any(word in text_lower for word in ['prayer', 'pray', 'ask']):
            hashtags.append('#Prayer')
        
        # Add general Christian hashtags
        general_tags = ['#Jesus', '#God', '#Christianity', '#Gospel', '#Scripture']
        hashtags.extend(random.sample(general_tags, min(2, len(general_tags))))
        
        # Limit to avoid overwhelming
        selected_tags = hashtags[:6]
        return ' '.join(selected_tags)

    def _get_relevant_emoji(self, verse_text: str) -> str:
        """Get relevant emoji based on verse content"""
        text_lower = verse_text.lower()
        
        if any(word in text_lower for word in ['love', 'beloved', 'heart']):
            return '💕'
        elif any(word in text_lower for word in ['peace', 'rest', 'calm']):
            return '☮️'
        elif any(word in text_lower for word in ['light', 'shine', 'bright']):
            return '✨'
        elif any(word in text_lower for word in ['strength', 'strong', 'power']):
            return '💪'
        elif any(word in text_lower for word in ['joy', 'rejoice', 'glad']):
            return '😊'
        elif any(word in text_lower for word in ['prayer', 'pray', 'ask']):
            return '🙏'
        elif any(word in text_lower for word in ['crown', 'king', 'throne']):
            return '👑'
        elif any(word in text_lower for word in ['shepherd', 'sheep', 'flock']):
            return '🐑'
        else:
            return '🙏'  # Default prayer hands

    def _ensure_tweet_length(self, tweet: str) -> str:
        """Ensure tweet fits Twitter's character limit"""
        if len(tweet) <= 280:
            return tweet
        
        # Try to truncate gracefully
        if len(tweet) > 280:
            # Find last complete sentence or phrase
            truncated = tweet[:277] + "..."
            return truncated

    def _has_posted_today(self, today: date) -> bool:
        """Check if we've already posted today"""
        try:
            results = self.db.execute_query(
                'SELECT id FROM daily_posts WHERE date = %s' if self.db.is_postgres else 
                'SELECT id FROM daily_posts WHERE date = ?', 
                (today,)
            )
            return len(results) > 0
            
        except Exception as e:
            logger.error(f"Error checking if posted today: {e}")
            return False

    def _record_daily_post(self, today: date, verse_data: Dict, tweet_id: str, force=False, reply_id=None):
        """Record today's post in the database"""
        try:
            if force:
                # In force mode, update existing record or insert new one
                if self.db.is_postgres:
                    self.db.execute_update('''
                        INSERT INTO daily_posts 
                        (date, verse_reference, verse_text, tweet_id, reply_tweet_id, posted_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (date) DO UPDATE SET
                            verse_reference = EXCLUDED.verse_reference,
                            verse_text = EXCLUDED.verse_text,
                            tweet_id = EXCLUDED.tweet_id,
                            reply_tweet_id = EXCLUDED.reply_tweet_id,
                            posted_at = EXCLUDED.posted_at
                    ''', (today, verse_data['reference'], verse_data['text'], tweet_id, reply_id, datetime.now()))
                else:
                    self.db.execute_update('''
                        INSERT OR REPLACE INTO daily_posts 
                        (date, verse_reference, verse_text, tweet_id, reply_tweet_id, posted_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (today, verse_data['reference'], verse_data['text'], tweet_id, reply_id, datetime.now()))
            else:
                # Normal mode, only insert if not exists
                if self.db.is_postgres:
                    self.db.execute_update('''
                        INSERT INTO daily_posts 
                        (date, verse_reference, verse_text, tweet_id, reply_tweet_id, posted_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (today, verse_data['reference'], verse_data['text'], tweet_id, reply_id, datetime.now()))
                else:
                    self.db.execute_update('''
                        INSERT INTO daily_posts 
                        (date, verse_reference, verse_text, tweet_id, reply_tweet_id, posted_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (today, verse_data['reference'], verse_data['text'], tweet_id, reply_id, datetime.now()))
            
        except Exception as e:
            logger.error(f"Error recording daily post: {e}")

    def get_posting_history(self, days: int = 7) -> list:
        """Get recent posting history"""
        try:
            results = self.db.execute_query('''
                SELECT date, verse_reference, tweet_id, posted_at
                FROM daily_posts 
                ORDER BY date DESC 
                LIMIT %s
            ''' if self.db.is_postgres else '''
                SELECT date, verse_reference, tweet_id, posted_at
                FROM daily_posts 
                ORDER BY date DESC 
                LIMIT ?
            ''', (days,))
            
            return [
                {
                    'date': row['date'],
                    'verse_reference': row['verse_reference'],
                    'tweet_id': row['tweet_id'],
                    'posted_at': row['posted_at']
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting posting history: {e}")
            return []

    def get_popular_verses(self, days: int = 30) -> list:
        """Get most popular recent verses based on engagement (placeholder)"""
        # This would require Twitter API v2 metrics
        # For now, return recent posts
        return self.get_posting_history(days)

    def schedule_themed_week(self, theme: str) -> bool:
        """Schedule a week of verses around a specific theme"""
        try:
            # This would implement themed posting
            # For example: "Hope Week", "Love Week", "Strength Week"
            themes = {
                'hope': ['hope', 'future', 'plans'],
                'love': ['love', 'beloved', 'compassion'], 
                'strength': ['strength', 'power', 'courage'],
                'peace': ['peace', 'rest', 'calm'],
                'joy': ['joy', 'rejoice', 'gladness']
            }
            
            if theme.lower() in themes:
                keywords = themes[theme.lower()]
                # Search for verses matching the theme
                verses = []
                for keyword in keywords:
                    theme_verses = self.bible_api.search_verses(keyword, limit=2)
                    verses.extend(theme_verses)
                
                # This could be extended to actually schedule posts
                logger.info(f"Found {len(verses)} verses for theme '{theme}'")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error scheduling themed week: {e}")
            return False
