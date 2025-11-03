"""
Twitter API integration for posting and monitoring mentions
"""
import tweepy
import logging
from typing import List, Dict, Optional
# Use cloud config if available, fallback to local config
try:
    import config_cloud as config
except ImportError:
    import config
import time

logger = logging.getLogger(__name__)

class TwitterAPI:
    # Class-level counter for API read calls (resets on restart)
    _read_call_count = 0
    _read_call_limit = 100  # Monthly limit for free tier
    
    def __init__(self, dry_run=False):
        self.api_key = config.TWITTER_API_KEY
        self.api_secret = config.TWITTER_API_SECRET
        self.access_token = config.TWITTER_ACCESS_TOKEN
        self.access_token_secret = config.TWITTER_ACCESS_TOKEN_SECRET
        self.bearer_token = config.TWITTER_BEARER_TOKEN
        self.client_id = getattr(config, 'TWITTER_CLIENT_ID', None)
        self.client_secret = getattr(config, 'TWITTER_CLIENT_SECRET', None)
        
        # Dry run mode - simulates posting without actually doing it
        self.dry_run = dry_run
        
        # Always initialize both OAuth 2.0 and 1.0a for maximum compatibility
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True
        )
        
        # Also initialize v1.1 API as fallback
        auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
        
        if self.client_id and self.client_secret:
            logger.info("Using OAuth 2.0 authentication with v1.1 fallback")
        else:
            logger.info("Using OAuth 1.0a authentication")
        
        self.bot_username = config.BOT_USERNAME
        self.user_id = config.TWITTER_USER_ID  # Set from config - never changes
        
    def verify_credentials(self) -> bool:
        """Verify that the API credentials are working"""
        try:
            # Skip v2 API auth check (requires User Context, we only have App-Only)
            # Go directly to v1.1 API which works with our auth setup
            if hasattr(self, 'api_v1'):
                user = self.api_v1.verify_credentials()
                if user:
                    logger.info(f"Successfully authenticated as @{user.screen_name} (OAuth 1.0a)")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to verify credentials: {e}")
            return False
    
    def post_tweet(self, text: str, media_path: Optional[str] = None) -> Optional[str]:
        """Post a tweet and return the tweet ID"""
        try:
            if len(text) > 280:
                logger.warning(f"Tweet text too long ({len(text)} chars), truncating...")
                text = text[:277] + "..."
            
            if self.dry_run:
                # Simulate posting without actually doing it
                fake_tweet_id = f"dry_run_{int(time.time())}"
                logger.info(f"🏃‍♂️ DRY RUN - Would post tweet: {fake_tweet_id}")
                logger.info(f"📝 Tweet content: {text}")
                if media_path:
                    logger.info(f"📷 Would include media: {media_path}")
                return fake_tweet_id
            
            # Try v2 API first (OAuth 2.0)
            if hasattr(self, 'client') and self.client_id:
                try:
                    if media_path:
                        # For now, skip media with v2 API
                        logger.warning("Media upload not implemented for v2 API, posting text only")
                    
                    response = self.client.create_tweet(text=text)
                    if response.data:
                        tweet_id = response.data['id']
                        logger.info(f"Successfully posted tweet via v2 API: {tweet_id}")
                        return str(tweet_id)
                except Exception as e:
                    logger.warning(f"v2 API posting failed: {e}, trying v1.1...")
            
            # Fallback to v1.1 API
            if hasattr(self, 'api_v1'):
                if media_path:
                    # Upload media first
                    media = self.api_v1.media_upload(media_path)
                    tweet = self.api_v1.update_status(status=text, media_ids=[media.media_id])
                else:
                    # Simple status update
                    tweet = self.api_v1.update_status(text)
                
                logger.info(f"Successfully posted tweet via v1.1 API: {tweet.id}")
                return str(tweet.id)
            
            logger.error("No valid API client available for posting")
            return None
            
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return None
    
    def get_mentions_tweepy(self, since_id: Optional[str] = None, count: int = 20) -> List[Dict]:
        """Get recent mentions of the bot"""
        try:
            mentions = []
            
            # Use v1.1 mentions_timeline (the correct and documented method)
            if hasattr(self, 'api_v1'):
                try:
                    logger.info(f"Getting mentions via v1.1 mentions_timeline API")
                    
                    # Use keyword arguments as required in tweepy v4
                    kwargs = {'count': count, 'include_entities': True, 'tweet_mode': 'extended'}
                    if since_id:
                        kwargs['since_id'] = since_id
                        logger.info(f"Using since_id: {since_id}")
                    
                    logger.info(f"v1.1 mentions_timeline parameters: {kwargs}")
                    tweets = self.api_v1.mentions_timeline(**kwargs)
                    logger.info(f"v1.1 API returned {len(tweets)} tweets")
                    
                    for tweet in tweets:
                        mention_data = {
                            'id': str(tweet.id),
                            'text': tweet.full_text if hasattr(tweet, 'full_text') else tweet.text,
                            'author_id': str(tweet.author.id),
                            'created_at': tweet.created_at,
                            'conversation_id': str(tweet.id),  # v1.1 doesn't have conversation_id
                            'in_reply_to_user_id': str(tweet.in_reply_to_user_id) if tweet.in_reply_to_user_id else None,
                            'original_tweet': None  # v1.1 API doesn't support expansions, will require separate call if needed
                        }
                        mentions.append(mention_data)
                        logger.info(f"Found mention: {tweet.full_text[:50] if hasattr(tweet, 'full_text') else tweet.text[:50]}... from @{tweet.author.screen_name}")
                        
                    logger.info(f"Found {len(mentions)} mentions via v1.1 mentions_timeline")
                    return mentions
                    
                except Exception as e:
                    logger.warning(f"v1.1 mentions_timeline failed: {e}, trying search fallback...")
            
            # Fallback to v2 search API
                
                # Try alternative search without filters
                try:
                    alt_query = self.bot_username  # Just the username without @
                    logger.info(f"Trying alternative search with query: '{alt_query}'")
                    
                    alt_kwargs = {
                        'query': alt_query,
                        'max_results': min(count, 100),
                        'tweet_fields': ['created_at', 'author_id', 'conversation_id', 'in_reply_to_user_id']
                    }
                    if since_id:
                        alt_kwargs['since_id'] = since_id
                        
                    alt_tweets = self.client.search_recent_tweets(**alt_kwargs)
                    logger.info(f"Alternative search returned: {type(alt_tweets)}, has data: {hasattr(alt_tweets, 'data') if alt_tweets else False}")
                    
                    if alt_tweets and hasattr(alt_tweets, 'data') and alt_tweets.data:
                        logger.info(f"Alternative search found {len(alt_tweets.data)} potential mentions")
                        for tweet in alt_tweets.data:
                            # Filter for actual mentions in the text
                            if f"@{self.bot_username.lower()}" in tweet.text.lower():
                                mention_data = {
                                    'id': tweet.id,
                                    'text': tweet.text,
                                    'author_id': tweet.author_id,
                                    'created_at': tweet.created_at,
                                    'conversation_id': tweet.conversation_id,
                                    'in_reply_to_user_id': tweet.in_reply_to_user_id,
                                    'original_tweet': None  # Search fallback doesn't support expansions
                                }
                                mentions.append(mention_data)
                                logger.info(f"Found mention via alternative search: {mention_data}")
                        
                        if mentions:
                            logger.info(f"Found {len(mentions)} mentions via alternative search")
                            return mentions
                            
                except Exception as alt_e:
                    logger.warning(f"Alternative search also failed: {alt_e}, trying v1.1...")
            
            # Fallback to v1.1 API
            if hasattr(self, 'api_v1'):
                kwargs = {'count': count, 'include_entities': True}
                if since_id:
                    kwargs['since_id'] = since_id
                    
                tweets = self.api_v1.mentions_timeline(**kwargs)
                
                for tweet in tweets:
                    mentions.append({
                        'id': str(tweet.id),
                        'text': tweet.text,
                        'author_id': str(tweet.author.id),
                        'created_at': tweet.created_at,
                        'conversation_id': str(tweet.id),  # v1.1 doesn't have conversation_id
                        'in_reply_to_user_id': str(tweet.in_reply_to_user_id) if tweet.in_reply_to_user_id else None,
                        'original_tweet': None  # v1.1 fallback doesn't support expansions
                    })
                    
                logger.info(f"Found {len(mentions)} mentions via v1.1 API")
                return mentions
            
            logger.info(f"Retrieved {len(mentions)} mentions")
            return mentions
            
        except Exception as e:
            logger.error(f"Failed to get mentions: {e}")
            return []
    
    def get_mentions(self, since_id: Optional[str] = None, count: int = 20) -> List[Dict]:
        """Get recent mentions using direct HTTP requests
        
        WARNING: X API Free tier allows only 100 API calls per MONTH
        Use this method sparingly - recommended: once per day maximum
        """
        try:
            import requests
            
            # Use user ID from config (no API calls needed)
            logger.info(f"Using user ID from config for mentions: {self.user_id}")
            
            # Direct HTTP request to X API v2 mentions endpoint
            url = f"https://api.x.com/2/users/{self.user_id}/mentions"
            
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "max_results": min(count, 100),
                "tweet.fields": "created_at,author_id,conversation_id,in_reply_to_user_id,referenced_tweets",
                "expansions": "referenced_tweets.id"
            }
            
            if since_id:
                params["since_id"] = since_id
                logger.info(f"Using since_id: {since_id}")
            
            logger.info(f"Making direct HTTP request to: {url}")
            logger.info(f"Request parameters: {params}")
            
            response = requests.get(url, headers=headers, params=params)
            logger.info(f"HTTP Response status: {response.status_code}")
            
            # Log rate limit headers for debugging and monitoring
            rate_limit_headers = {}
            for header_name in response.headers:
                if 'rate' in header_name.lower() or 'limit' in header_name.lower():
                    rate_limit_headers[header_name] = response.headers[header_name]
            
            if rate_limit_headers:
                logger.info(f"🔢 API USAGE - Rate limit headers: {rate_limit_headers}")
                # Extract key info for monitoring
                remaining = rate_limit_headers.get('x-rate-limit-remaining', 'unknown')
                reset_time = rate_limit_headers.get('x-rate-limit-reset', 'unknown')
                logger.warning(f"📊 API BUDGET: {remaining} calls remaining until reset at {reset_time}")
            else:
                logger.info("No rate limit headers found")
            
            # Track and log every API call for budget tracking
            TwitterAPI._read_call_count += 1
            remaining_budget = TwitterAPI._read_call_limit - TwitterAPI._read_call_count
            logger.warning(f"💰 API READ CALL #{TwitterAPI._read_call_count}: get_mentions() - {remaining_budget} calls remaining this month (limit: {TwitterAPI._read_call_limit})")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data keys: {list(data.keys()) if data else 'None'}")
                
                # Build a lookup map for referenced tweets (original tweets)
                referenced_tweets_map = {}
                if 'includes' in data and 'tweets' in data['includes']:
                    for ref_tweet in data['includes']['tweets']:
                        referenced_tweets_map[str(ref_tweet['id'])] = {
                            'id': str(ref_tweet['id']),
                            'text': ref_tweet['text'],
                            'author_id': str(ref_tweet['author_id']),
                            'created_at': ref_tweet['created_at']
                        }
                    logger.info(f"Found {len(referenced_tweets_map)} referenced tweets in includes")
                
                mentions = []
                if 'data' in data and data['data']:
                    logger.info(f"Found {len(data['data'])} mentions via direct HTTP")
                    
                    for tweet_data in data['data']:
                        mention_data = {
                            'id': str(tweet_data['id']),
                            'text': tweet_data['text'],
                            'author_id': str(tweet_data['author_id']),
                            'created_at': tweet_data['created_at'],
                            'conversation_id': str(tweet_data.get('conversation_id', tweet_data['id'])),
                            'in_reply_to_user_id': str(tweet_data['in_reply_to_user_id']) if tweet_data.get('in_reply_to_user_id') else None,
                            'original_tweet': None  # Will be populated if this is a reply
                        }
                        
                        # If this tweet has referenced tweets (i.e., it's a reply), add the original tweet
                        if 'referenced_tweets' in tweet_data:
                            for ref_tweet in tweet_data['referenced_tweets']:
                                if ref_tweet['type'] == 'replied_to':
                                    ref_tweet_id = str(ref_tweet['id'])
                                    if ref_tweet_id in referenced_tweets_map:
                                        mention_data['original_tweet'] = referenced_tweets_map[ref_tweet_id]
                                        logger.info(f"Mention {mention_data['id']} has original tweet context: {mention_data['original_tweet']['text'][:50]}...")
                                        break
                        
                        mentions.append(mention_data)
                        logger.info(f"Found mention: {tweet_data['text'][:50]}... from user {tweet_data['author_id']}")
                    
                    return mentions
                else:
                    logger.info("No mentions found in response data")
                    return []
            
            elif response.status_code == 429:
                logger.warning(f"Rate limit exceeded (429). Response: {response.text}")
                return []
            else:
                logger.error(f"HTTP request failed with status {response.status_code}: {response.text}")
                # Fallback to tweepy method
                logger.info("Falling back to tweepy method...")
                return self.get_mentions_tweepy(since_id=since_id, count=count)
                
        except Exception as e:
            logger.error(f"Direct HTTP mentions request failed: {e}")
            # Fallback to tweepy method
            logger.info("Falling back to tweepy method...")
            return self.get_mentions_tweepy(since_id=since_id, count=count)
    
    def reply_to_tweet(self, tweet_id: str, reply_text: str) -> Optional[str]:
        """Reply to a specific tweet"""
        try:
            if len(reply_text) > 280:
                logger.warning(f"Reply text too long ({len(reply_text)} chars), truncating...")
                reply_text = reply_text[:277] + "..."
            
            if self.dry_run:
                # Simulate replying without actually doing it
                fake_reply_id = f"dry_run_reply_{int(time.time())}"
                logger.info(f"🏃‍♂️ DRY RUN - Would reply to tweet {tweet_id}: {fake_reply_id}")
                logger.info(f"💬 Reply content: {reply_text}")
                return fake_reply_id
            
            # Try v2 API first (OAuth 2.0)
            if hasattr(self, 'client') and self.client_id:
                try:
                    response = self.client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)
                    if response.data:
                        reply_id = response.data['id']
                        logger.info(f"Successfully replied via v2 API to tweet {tweet_id}: {reply_id}")
                        return str(reply_id)
                except Exception as e:
                    logger.warning(f"v2 API reply failed (likely access level issue): {e}")
                    logger.info("Falling back to v1.1 API for reply...")
            
            # Fallback to v1.1 API
            if hasattr(self, 'api_v1'):
                logger.info("Attempting v1.1 API reply...")
                logger.info(f"Using v1.1 endpoint: POST statuses/update with in_reply_to_status_id={tweet_id}")
                reply = self.api_v1.update_status(
                    status=reply_text,
                    in_reply_to_status_id=tweet_id,
                    auto_populate_reply_metadata=True
                )
                
                logger.info(f"Successfully replied via v1.1 API to tweet {tweet_id}: {reply.id}")
                return str(reply.id)
            else:
                logger.error("api_v1 client not available - missing OAuth 1.0a credentials?")
            
            logger.error("No valid API client available for replying")
            return None
            
        except Exception as e:
            logger.error(f"Failed to reply to tweet {tweet_id}: {e}")
            return None
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Get information about a user"""
        try:
            user = self.client.get_user(
                id=user_id,
                user_fields=['username', 'name', 'description', 'public_metrics']
            )
            
            if user.data:
                return {
                    'id': user.data.id,
                    'username': user.data.username,
                    'name': user.data.name,
                    'description': user.data.description,
                    'followers_count': user.data.public_metrics['followers_count'],
                    'following_count': user.data.public_metrics['following_count']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user info for {user_id}: {e}")
            return None
    
    def search_tweets(self, query: str, count: int = 10, include_thread_context: bool = False) -> List[Dict]:
        """Search for tweets containing specific keywords using direct HTTP requests
        
        WARNING: X API Free tier allows only 100 API calls per MONTH
        Use this method very sparingly - recommended: few times per week maximum
        
        Args:
            query: Search query string
            count: Number of tweets to return (max 100)
            include_thread_context: If True, fetch full thread context for replies
        
        Returns:
            List of tweet dictionaries with optional thread context
        """
        try:
            import requests
            
            # Ensure count is within Twitter API limits (10-100)
            api_count = max(10, min(count, 100))
            
            # Direct HTTP request to X API v2 search endpoint
            url = "https://api.x.com/2/tweets/search/recent"
            
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "query": query,
                "max_results": api_count,
                "tweet.fields": "created_at,author_id,public_metrics,conversation_id,in_reply_to_user_id"
            }
            
            logger.info(f"Making direct HTTP search request to: {url}")
            logger.info(f"Search query: '{query}', max_results: {api_count}")
            
            response = requests.get(url, headers=headers, params=params)
            logger.info(f"HTTP Response status: {response.status_code}")
            
            # Log rate limit headers for debugging and monitoring
            rate_limit_headers = {}
            for header_name in response.headers:
                if 'rate' in header_name.lower() or 'limit' in header_name.lower():
                    rate_limit_headers[header_name] = response.headers[header_name]
            
            if rate_limit_headers:
                logger.info(f"🔢 API USAGE - Rate limit headers: {rate_limit_headers}")
                # Extract key info for monitoring
                remaining = rate_limit_headers.get('x-rate-limit-remaining', 'unknown')
                reset_time = rate_limit_headers.get('x-rate-limit-reset', 'unknown')
                logger.warning(f"📊 API BUDGET: {remaining} calls remaining until reset at {reset_time}")
            
            # Track and log every API call for budget tracking
            TwitterAPI._read_call_count += 1
            remaining_budget = TwitterAPI._read_call_limit - TwitterAPI._read_call_count
            logger.warning(f"💰 API READ CALL #{TwitterAPI._read_call_count}: search_tweets('{query}') - {remaining_budget} calls remaining this month (limit: {TwitterAPI._read_call_limit})")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data keys: {list(data.keys()) if data else 'None'}")
                
                results = []
                if 'data' in data and data['data']:
                    logger.info(f"Found {len(data['data'])} tweets via direct HTTP search")
                    
                    for tweet_data in data['data']:
                        tweet_result = {
                            'id': str(tweet_data['id']),
                            'text': tweet_data['text'],
                            'author_id': str(tweet_data['author_id']),
                            'created_at': tweet_data['created_at'],
                            'public_metrics': tweet_data.get('public_metrics', {}),
                            'conversation_id': str(tweet_data['conversation_id']),
                            'in_reply_to_user_id': str(tweet_data['in_reply_to_user_id']) if tweet_data.get('in_reply_to_user_id') else None,
                            'is_reply': str(tweet_data['id']) != str(tweet_data['conversation_id'])
                        }
                        
                        # If this is a reply and we want thread context, fetch it
                        if tweet_result['is_reply'] and include_thread_context:
                            thread_context = self.get_thread_context(tweet_result['conversation_id'])
                            tweet_result['thread_context'] = thread_context
                        
                        results.append(tweet_result)
                        logger.info(f"Found tweet: {tweet_data['text'][:50]}... from user {tweet_data['author_id']}")
                    
                    return results
                else:
                    logger.info("No tweets found in search response")
                    return []
            
            elif response.status_code == 429:
                logger.warning(f"Rate limit exceeded (429). Response: {response.text}")
                return []
            else:
                logger.error(f"HTTP search request failed with status {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Direct HTTP search request failed: {e}")
            return []
    
    def get_thread_context(self, conversation_id: str) -> Dict:
        """Get the entire thread/conversation for a given conversation ID
        
        Args:
            conversation_id: The ID of the original tweet in the conversation
            
        Returns:
            Dictionary containing the original tweet and all replies in chronological order
        """
        try:
            thread_context = {
                'original_tweet': None,
                'replies': [],
                'total_tweets': 0
            }
            
            # First, get the original tweet
            original_tweet = self.get_original_tweet(conversation_id)
            if original_tweet:
                thread_context['original_tweet'] = original_tweet
                thread_context['total_tweets'] += 1
            
            # Then search for all replies in this conversation
            # Use search to find replies to this conversation
            search_query = f"conversation_id:{conversation_id}"
            logger.info(f"Getting thread context with query: {search_query}")
            
            try:
                # Use direct HTTP request for searching conversation tweets
                import requests
                
                url = "https://api.x.com/2/tweets/search/recent"
                headers = {
                    "Authorization": f"Bearer {self.bearer_token}",
                    "Content-Type": "application/json"
                }
                params = {
                    "query": search_query,
                    "max_results": 100,  # Get up to 100 tweets in the thread
                    "tweet.fields": "created_at,author_id,conversation_id,in_reply_to_user_id"
                }
                
                logger.info(f"Making direct HTTP request for conversation search: {url}")
                
                # Track this as a read call
                TwitterAPI._read_call_count += 1
                remaining_budget = TwitterAPI._read_call_limit - TwitterAPI._read_call_count
                logger.warning(f"💰 API READ CALL #{TwitterAPI._read_call_count}: get_thread_context({conversation_id}) - {remaining_budget} calls remaining this month")
                
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data']:
                        for tweet_data in data['data']:
                            # Skip the original tweet (we already have it)
                            if str(tweet_data['id']) != str(conversation_id):
                                reply_data = {
                                    'id': str(tweet_data['id']),
                                    'text': tweet_data['text'],
                                    'author_id': str(tweet_data['author_id']),
                                    'created_at': tweet_data['created_at'],
                                    'in_reply_to_user_id': str(tweet_data['in_reply_to_user_id']) if tweet_data.get('in_reply_to_user_id') else None
                                }
                                thread_context['replies'].append(reply_data)
                                thread_context['total_tweets'] += 1
                        
                        # Sort replies by creation time (chronological order)
                        thread_context['replies'].sort(key=lambda x: x['created_at'])
                        
                    logger.info(f"Found thread with {thread_context['total_tweets']} total tweets")
                elif response.status_code == 429:
                    logger.warning(f"Rate limit hit during thread search: {response.text}")
                else:
                    logger.warning(f"Thread search failed with status {response.status_code}: {response.text}")
                
            except Exception as search_e:
                logger.warning(f"Search for conversation failed: {search_e}, trying alternative method...")
                # If search fails, we still have the original tweet
                pass
                
            return thread_context
            
        except Exception as e:
            logger.error(f"Failed to get thread context for conversation {conversation_id}: {e}")
            return {'original_tweet': None, 'replies': [], 'total_tweets': 0}
    
    def get_original_tweet(self, conversation_id: str) -> Optional[Dict]:
        """Get just the original tweet from a conversation using direct HTTP requests
        
        Args:
            conversation_id: The ID of the original tweet
            
        Returns:
            Dictionary containing the original tweet data, or None if not found
        """
        try:
            import requests
            
            # Direct HTTP request to X API v2 get tweet endpoint
            url = f"https://api.x.com/2/tweets/{conversation_id}"
            
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "tweet.fields": "created_at,author_id,public_metrics,conversation_id"
            }
            
            logger.info(f"Making direct HTTP request to get original tweet: {url}")
            
            # Track this as a read call
            TwitterAPI._read_call_count += 1
            remaining_budget = TwitterAPI._read_call_limit - TwitterAPI._read_call_count
            logger.warning(f"💰 API READ CALL #{TwitterAPI._read_call_count}: get_original_tweet({conversation_id}) - {remaining_budget} calls remaining this month")
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    tweet_data = data['data']
                    return {
                        'id': str(tweet_data['id']),
                        'text': tweet_data['text'],
                        'author_id': str(tweet_data['author_id']),
                        'created_at': tweet_data['created_at'],
                        'public_metrics': tweet_data.get('public_metrics', {}),
                        'conversation_id': str(tweet_data['conversation_id'])
                    }
            
            elif response.status_code == 429:
                logger.warning(f"Rate limit exceeded getting original tweet {conversation_id}")
            else:
                logger.error(f"Failed to get original tweet {conversation_id}: status {response.status_code}, {response.text}")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get original tweet {conversation_id}: {e}")
            return None
    
    def like_tweet(self, tweet_id: str) -> bool:
        """Like a tweet"""
        try:
            self.api_v1.create_favorite(tweet_id)
            logger.info(f"Liked tweet {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to like tweet {tweet_id}: {e}")
            return False
    
    def retweet(self, tweet_id: str) -> bool:
        """Retweet a tweet"""
        try:
            self.api_v1.retweet(tweet_id)
            logger.info(f"Retweeted {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to retweet {tweet_id}: {e}")
            return False
    
    def delete_tweet(self, tweet_id: str) -> bool:
        """Delete a tweet"""
        try:
            self.api_v1.destroy_status(tweet_id)
            logger.info(f"Deleted tweet {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete tweet {tweet_id}: {e}")
            return False
    
    @classmethod
    def get_read_call_count(cls) -> Dict[str, int]:
        """Get current API read call statistics"""
        return {
            'count': cls._read_call_count,
            'limit': cls._read_call_limit,
            'remaining': cls._read_call_limit - cls._read_call_count,
            'percentage_used': round((cls._read_call_count / cls._read_call_limit) * 100, 1) if cls._read_call_limit > 0 else 0
        }
    
    @classmethod
    def reset_read_call_count(cls):
        """Reset the API call counter (useful for tracking monthly usage)"""
        cls._read_call_count = 0
        logger.info("API read call counter reset")
    
    def format_verse_tweet(self, verse_data: Dict) -> str:
        """Format a Bible verse for posting on Twitter"""
        reference = verse_data['reference']
        text = verse_data['text']
        version = verse_data['version']
        
        # Create the tweet text
        tweet_text = f'"{text}"\n\n{reference} ({version})\n\n#BibleVerse #Faith #Jesus #God #Christianity #DailyVerse'
        
        # Check if it fits in Twitter's character limit
        if len(tweet_text) <= 280:
            return tweet_text
        
        # If too long, try to trim the hashtags
        base_text = f'"{text}"\n\n{reference} ({version})'
        if len(base_text) <= 280:
            return base_text
        
        # If still too long, trim the verse text
        max_verse_length = 280 - len(f'"\n\n{reference} ({version})')
        if max_verse_length > 50:  # Ensure we have reasonable space for the verse
            trimmed_text = text[:max_verse_length-3] + "..."
            return f'"{trimmed_text}"\n\n{reference} ({version})'
        
        # Fallback: just reference
        return f'{reference} ({version})'
