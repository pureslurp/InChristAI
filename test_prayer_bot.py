#!/usr/bin/env python3
"""
Test suite for prayer bot functionality
"""
import logging
import sys
import argparse
from typing import List, Dict

# Use cloud config if available, fallback to local config
try:
    import config_cloud as config
except ImportError:
    import config

from twitter_api import TwitterAPI
from ai_responses import AIResponseGenerator
from tweet_models import Tweet, create_tweets_from_search_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

class PrayerBotTester:
    def __init__(self, dry_run=True, use_real_tweets=False):
        self.twitter_api = TwitterAPI(dry_run=dry_run)
        self.ai_generator = AIResponseGenerator()
        self.dry_run = dry_run
        self.use_real_tweets = use_real_tweets
        
    def test_prayer_search_workflow(self, search_term="pray", count=10):
        """Test the complete prayer search and response workflow"""
        try:
            logger.info("🧪 Starting Prayer Search Test")
            if self.use_real_tweets:
                logger.info("📡 Using REAL Twitter API calls")
            else:
                logger.info("🤖 Using MOCK data (no API calls)")
            logger.info("=" * 60)
            
            # Step 1: Get tweets (real or mock)
            if self.use_real_tweets:
                logger.info(f"📱 Step 1: Searching for '{search_term}' tweets...")
                tweets = self.twitter_api.search_tweets(search_term, count=count)
                
                if not tweets:
                    logger.warning("❌ No tweets found - might be rate limited")
                    return False
                    
                logger.info(f"✅ Found {len(tweets)} real tweets")
            else:
                logger.info(f"📱 Step 1: Creating mock '{search_term}' tweets...")
                tweets = self._create_mock_prayer_tweets()
                logger.info(f"✅ Created {len(tweets)} mock tweets")
            
            # Show sample tweets
            logger.info("\n📝 Sample tweets:")
            for i, tweet in enumerate(tweets[:3], 1):
                logger.info(f"  {i}. {tweet['text'][:80]}...")
                logger.info(f"      Author: {tweet['author_id']}, Is Reply: {tweet['is_reply']}")
            
            # Step 2: Run AI analysis
            logger.info("\n🤖 Step 2: Running 4-step AI analysis...")
            result = self.ai_generator.select_and_respond_to_tweet(tweets)
            
            if not result:
                logger.warning("❌ No suitable tweet found for spiritual response")
                return False
            
            # Step 3: Display results
            self._display_analysis_results(result)
            
            # Step 4: Handle response (dry run or real)
            self._handle_response(result)
            
            logger.info("\n🎉 Prayer Search Test Completed Successfully!")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ Prayer search test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_ai_filtering_only(self):
        """Test just the AI filtering and selection without responses"""
        try:
            logger.info("🧠 Testing AI Filtering and Selection")
            logger.info("=" * 50)
            
            # Use mock data with diverse content for filtering test
            tweets = self._create_diverse_test_tweets()
            logger.info(f"📊 Created {len(tweets)} diverse test tweets")
            
            # Show all tweets being analyzed
            logger.info("\n📝 All test tweets:")
            for i, tweet in enumerate(tweets, 1):
                logger.info(f"  {i}. {tweet['text'][:100]}...")
                logger.info(f"      Type: {self._classify_tweet_type(tweet)}")
            
            # Run selection only (no response generation)
            logger.info("\n🔍 Running AI tweet selection...")
            selected_tweet = self.ai_generator._ai_select_best_tweet(
                create_tweets_from_search_results(tweets)
            )
            
            if selected_tweet:
                logger.info(f"\n✅ AI Selected Tweet:")
                logger.info(f"   ID: {selected_tweet.id}")
                logger.info(f"   Text: {selected_tweet.text}")
                logger.info(f"   Reason: Best candidate for spiritual response")
            else:
                logger.info("\n❌ AI found no suitable tweets")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ AI filtering test failed: {e}")
            return False
    
    def test_mood_detection(self):
        """Test mood detection for various emotional states"""
        try:
            logger.info("😊 Testing Mood Detection")
            logger.info("=" * 40)
            
            test_cases = [
                ("I'm so scared about my surgery tomorrow", "afraid"),
                ("Feeling really anxious about everything lately", "anxious"),
                ("So lonely since moving to this new city", "lonely"),
                ("Lost my dad last week, heartbroken", "sad"),
                ("This whole situation makes me so angry!", "angry"),
                ("I don't know what to do anymore, so confused", "confused"),
                ("Everything seems pointless right now", "discouraged"),
                ("I feel terrible about what I did", "guilty"),
                ("Work is overwhelming me completely", "stressed"),
                ("There's no way out of this situation", "hopeless"),
                ("So thankful for all the support", "grateful"),
                ("Everyone else has it better than me", "jealous")
            ]
            
            correct_predictions = 0
            total_tests = len(test_cases)
            
            for i, (text, expected_mood) in enumerate(test_cases, 1):
                logger.info(f"\nTest {i}/{total_tests}:")
                logger.info(f"  Text: '{text}'")
                logger.info(f"  Expected: {expected_mood}")
                
                # Create mock tweet
                mock_tweet = Tweet({
                    'id': f'test_{i}',
                    'text': text,
                    'author_id': '1001',
                    'created_at': '2025-09-20T18:00:00.000Z',
                    'public_metrics': {},
                    'conversation_id': f'test_{i}',
                    'in_reply_to_user_id': None,
                    'is_reply': False
                })
                
                detected_mood = self.ai_generator._ai_determine_mood(mock_tweet)
                logger.info(f"  Detected: {detected_mood}")
                
                if detected_mood == expected_mood:
                    logger.info("  ✅ Correct!")
                    correct_predictions += 1
                else:
                    logger.info("  ❌ Incorrect")
            
            accuracy = (correct_predictions / total_tests) * 100
            logger.info(f"\n📊 Mood Detection Accuracy: {correct_predictions}/{total_tests} ({accuracy:.1f}%)")
            
            return accuracy >= 70  # Expect at least 70% accuracy
            
        except Exception as e:
            logger.error(f"❌ Mood detection test failed: {e}")
            return False
    
    def _display_analysis_results(self, result):
        """Display the complete analysis results"""
        logger.info("\n🎯 Analysis Results:")
        logger.info("=" * 40)
        logger.info(f"Selected Tweet ID: {result.selected_tweet.id}")
        logger.info(f"Selected Tweet Text: {result.selected_tweet.text}")
        logger.info(f"Author: {result.selected_tweet.author_id}")
        logger.info(f"Is Reply: {result.selected_tweet.is_reply}")
        
        if result.selected_tweet.is_reply:
            original_text = result.selected_tweet.get_original_tweet_text()
            if original_text:
                logger.info(f"Original Tweet: {original_text[:80]}...")
        
        logger.info(f"\nDetected Mood: {result.detected_mood}")
        
        logger.info(f"\nBible Verse:")
        logger.info(f"  Reference: {result.bible_verse['reference']} ({result.bible_verse['version']})")
        logger.info(f"  Text: {result.bible_verse['text']}")
        
        logger.info(f"\nGenerated Response ({len(result.response_text)} chars):")
        logger.info(f"  {result.response_text}")
    
    def _handle_response(self, result):
        """Handle the response based on dry run settings"""
        if self.dry_run:
            logger.info("\n🏃‍♂️ DRY RUN: Would reply to tweet with:")
            logger.info(f"   Tweet ID: {result.selected_tweet.id}")
            logger.info(f"   Response: {result.response_text}")
            logger.info("   (No actual posting performed)")
        else:
            logger.info("\n📤 Posting reply...")
            reply_id = self.twitter_api.reply_to_tweet(
                result.selected_tweet.id,
                result.response_text
            )
            if reply_id:
                logger.info(f"✅ Successfully posted reply: {reply_id}")
            else:
                logger.error("❌ Failed to post reply")
                return False
        return True
    
    def _classify_tweet_type(self, tweet):
        """Classify tweet type for display purposes"""
        text = tweet['text'].lower()
        
        if tweet['text'].startswith('RT @'):
            return "RETWEET (should avoid)"
        elif any(word in text for word in ['crypto', 'bitcoin', 'investment']):
            return "COMMERCIAL (should avoid)"
        elif any(word in text for word in ['political', 'politics', 'vote']):
            return "POLITICAL (should avoid)"
        elif any(word in text for word in ['pray', 'prayer', 'prayers']):
            return "PRAYER REQUEST (good candidate)"
        elif any(word in text for word in ['anxious', 'scared', 'lonely', 'hopeless']):
            return "EMOTIONAL NEED (good candidate)"
        else:
            return "NEUTRAL"
    
    def _create_mock_prayer_tweets(self) -> List[Dict]:
        """Create mock prayer-related tweets for testing"""
        return [
            {
                'id': '1234567890123456001',
                'text': 'Going through a really difficult time right now. Could really use some prayers and positive thoughts. Feeling so overwhelmed with everything.',
                'author_id': '1001',
                'created_at': '2025-09-20T18:40:00.000Z',
                'public_metrics': {'like_count': 5, 'retweet_count': 2, 'reply_count': 1},
                'conversation_id': '1234567890123456001',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            {
                'id': '1234567890123456002', 
                'text': 'RT @someone: Just wanted to say that prayer works! God is good! #blessed #faith',
                'author_id': '1002',
                'created_at': '2025-09-20T18:35:00.000Z',
                'public_metrics': {'like_count': 10, 'retweet_count': 5, 'reply_count': 0},
                'conversation_id': '1234567890123456002',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            {
                'id': '1234567890123456003',
                'text': 'My mom is having surgery tomorrow. Please pray for her recovery. She means everything to me and I\'m so scared.',
                'author_id': '1003',
                'created_at': '2025-09-20T18:30:00.000Z',
                'public_metrics': {'like_count': 15, 'retweet_count': 3, 'reply_count': 8},
                'conversation_id': '1234567890123456003',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            {
                'id': '1234567890123456004',
                'text': 'Lost my job today after 10 years. Not sure how I\'m going to pay rent. Feeling hopeless and could use some prayers right now.',
                'author_id': '1004',
                'created_at': '2025-09-20T18:25:00.000Z',
                'public_metrics': {'like_count': 25, 'retweet_count': 1, 'reply_count': 12},
                'conversation_id': '1234567890123456004',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            {
                'id': '1234567890123456005',
                'text': 'Can anyone recommend a good cryptocurrency investment? Looking to make some quick money! #crypto #bitcoin #trading',
                'author_id': '1005',
                'created_at': '2025-09-20T18:20:00.000Z',
                'public_metrics': {'like_count': 2, 'retweet_count': 0, 'reply_count': 0},
                'conversation_id': '1234567890123456005',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            {
                'id': '1234567890123456006',
                'text': 'Struggling with anxiety lately. The world feels so chaotic and I can\'t shake this feeling of dread. Anyone else feeling this way?',
                'author_id': '1006',
                'created_at': '2025-09-20T18:15:00.000Z',
                'public_metrics': {'like_count': 8, 'retweet_count': 2, 'reply_count': 5},
                'conversation_id': '1234567890123456006',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            {
                'id': '1234567890123456007',
                'text': 'This political situation is absolutely ridiculous! These politicians are all corrupt! #politics #angry #vote',
                'author_id': '1007',
                'created_at': '2025-09-20T18:10:00.000Z',
                'public_metrics': {'like_count': 50, 'retweet_count': 20, 'reply_count': 30},
                'conversation_id': '1234567890123456007',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            {
                'id': '1234567890123456008',
                'text': 'Thank you to everyone who has been praying for my family during this difficult time. Your support means the world to us.',
                'author_id': '1008',
                'created_at': '2025-09-20T18:05:00.000Z',
                'public_metrics': {'like_count': 30, 'retweet_count': 5, 'reply_count': 15},
                'conversation_id': '1234567890123456008',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            {
                'id': '1234567890123456009',
                'text': 'Feeling so lonely since moving to this new city. Don\'t know anyone here and it\'s harder than I thought it would be.',
                'author_id': '1009',
                'created_at': '2025-09-20T18:00:00.000Z',
                'public_metrics': {'like_count': 12, 'retweet_count': 1, 'reply_count': 6},
                'conversation_id': '1234567890123456009',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            {
                'id': '1234567890123456010',
                'text': 'Why do bad things happen to good people? Really questioning everything right now. Life doesn\'t make sense anymore.',
                'author_id': '1010',
                'created_at': '2025-09-20T17:55:00.000Z',
                'public_metrics': {'like_count': 18, 'retweet_count': 3, 'reply_count': 9},
                'conversation_id': '1234567890123456010',
                'in_reply_to_user_id': None,
                'is_reply': False
            }
        ]
    
    def _create_diverse_test_tweets(self) -> List[Dict]:
        """Create diverse tweets specifically for testing AI filtering"""
        return [
            # GOOD candidates
            {
                'id': 'good_1',
                'text': 'Please pray for my sick grandmother. She\'s all I have left.',
                'author_id': '2001',
                'created_at': '2025-09-20T18:00:00.000Z',
                'public_metrics': {},
                'conversation_id': 'good_1',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            {
                'id': 'good_2', 
                'text': 'Having panic attacks every day. Don\'t know how to cope anymore.',
                'author_id': '2002',
                'created_at': '2025-09-20T18:00:00.000Z',
                'public_metrics': {},
                'conversation_id': 'good_2',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            # BAD candidates
            {
                'id': 'bad_1',
                'text': 'RT @someone: Check out this amazing crypto opportunity! #bitcoin #investment',
                'author_id': '2003',
                'created_at': '2025-09-20T18:00:00.000Z',
                'public_metrics': {},
                'conversation_id': 'bad_1',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            {
                'id': 'bad_2',
                'text': 'These politicians are all idiots! Vote them all out! #politics #angry',
                'author_id': '2004',
                'created_at': '2025-09-20T18:00:00.000Z',
                'public_metrics': {},
                'conversation_id': 'bad_2',
                'in_reply_to_user_id': None,
                'is_reply': False
            },
            # NEUTRAL
            {
                'id': 'neutral_1',
                'text': 'Beautiful sunset today! Nature is amazing.',
                'author_id': '2005',
                'created_at': '2025-09-20T18:00:00.000Z',
                'public_metrics': {},
                'conversation_id': 'neutral_1',
                'in_reply_to_user_id': None,
                'is_reply': False
            }
        ]

def main():
    """Main entry point for prayer bot testing"""
    parser = argparse.ArgumentParser(description='Prayer Bot Test Suite')
    parser.add_argument('test_type', choices=['workflow', 'filtering', 'mood', 'all'], 
                       help='Type of test to run')
    parser.add_argument('--real-tweets', action='store_true', 
                       help='Use real Twitter API calls instead of mock data')
    parser.add_argument('--live-posting', action='store_true',
                       help='Actually post responses (not dry run)')
    parser.add_argument('--search-term', default='pray',
                       help='Search term for tweet lookup (default: pray)')
    parser.add_argument('--count', type=int, default=10,
                       help='Number of tweets to fetch (default: 10)')
    
    args = parser.parse_args()
    
    # Configure test settings
    dry_run = not args.live_posting
    use_real_tweets = args.real_tweets
    
    # Initialize tester
    tester = PrayerBotTester(dry_run=dry_run, use_real_tweets=use_real_tweets)
    
    # Run tests
    success = True
    
    if args.test_type == 'workflow' or args.test_type == 'all':
        logger.info("🔄 Running Workflow Test")
        success &= tester.test_prayer_search_workflow(args.search_term, args.count)
    
    if args.test_type == 'filtering' or args.test_type == 'all':
        logger.info("\n🔍 Running Filtering Test")  
        success &= tester.test_ai_filtering_only()
    
    if args.test_type == 'mood' or args.test_type == 'all':
        logger.info("\n😊 Running Mood Detection Test")
        success &= tester.test_mood_detection()
    
    # Summary
    if success:
        logger.info("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
