"""
Tweet data models for better organization and type safety
"""
from typing import Dict, Optional, List
from datetime import datetime

class Tweet:
    """Represents a Twitter tweet with all its metadata"""
    
    def __init__(self, tweet_data: Dict):
        """Initialize from tweet dictionary returned by search_tweets"""
        self.id = str(tweet_data['id'])
        self.text = tweet_data['text']
        self.author_id = str(tweet_data['author_id'])
        self.created_at = tweet_data['created_at']
        self.public_metrics = tweet_data.get('public_metrics', {})
        self.conversation_id = str(tweet_data['conversation_id'])
        self.in_reply_to_user_id = tweet_data.get('in_reply_to_user_id')
        self.is_reply = tweet_data.get('is_reply', False)
        self.thread_context = tweet_data.get('thread_context')
        
        # Additional computed properties
        self.is_retweet = self.text.startswith('RT @')
        self.like_count = self.public_metrics.get('like_count', 0)
        self.retweet_count = self.public_metrics.get('retweet_count', 0)
        self.reply_count = self.public_metrics.get('reply_count', 0)
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return f"Tweet({self.id}): {self.text[:50]}..."
    
    def to_dict(self) -> Dict:
        """Convert back to dictionary format"""
        return {
            'id': self.id,
            'text': self.text,
            'author_id': self.author_id,
            'created_at': self.created_at,
            'public_metrics': self.public_metrics,
            'conversation_id': self.conversation_id,
            'in_reply_to_user_id': self.in_reply_to_user_id,
            'is_reply': self.is_reply,
            'thread_context': self.thread_context
        }
    
    def get_original_tweet_text(self) -> Optional[str]:
        """Get the original tweet text if this is a reply with thread context"""
        if self.is_reply and self.thread_context:
            original = self.thread_context.get('original_tweet')
            if original:
                return original.get('text')
        return None
    
    def get_thread_summary(self) -> str:
        """Get a summary of the thread context for AI analysis"""
        if not self.is_reply or not self.thread_context:
            return ""
        
        original = self.thread_context.get('original_tweet')
        if original:
            return f"(Reply to: \"{original['text'][:80]}...\")"
        return "(Reply to unavailable tweet)"
    
    def has_spiritual_keywords(self) -> bool:
        """Quick check if tweet contains spiritual/prayer keywords"""
        spiritual_keywords = [
            'pray', 'prayer', 'prayers', 'praying', 'god', 'lord', 'jesus',
            'faith', 'bible', 'church', 'christian', 'blessed', 'blessing'
        ]
        text_lower = self.text.lower()
        return any(keyword in text_lower for keyword in spiritual_keywords)
    
    def has_emotional_keywords(self) -> bool:
        """Quick check if tweet contains emotional need keywords"""
        emotional_keywords = [
            'struggling', 'difficult', 'anxious', 'worried', 'scared',
            'hurt', 'pain', 'lost', 'confused', 'broken', 'hopeless',
            'alone', 'lonely', 'stressed', 'overwhelmed', 'depressed'
        ]
        text_lower = self.text.lower()
        return any(keyword in text_lower for keyword in emotional_keywords)
    
    def should_avoid(self) -> bool:
        """Check if this tweet should be avoided for responses"""
        avoid_keywords = [
            'politics', 'political', 'democrat', 'republican', 'vote', 'election',
            'crypto', 'bitcoin', 'nft', 'trading', 'investment', 'promotion',
            'follow me', 'check out', 'link in bio', 'spam', 'scam',
            'hate', 'angry', 'stupid', 'idiot', 'dumb'
        ]
        text_lower = self.text.lower()
        
        # Avoid retweets
        if self.is_retweet:
            return True
            
        # Avoid tweets with problematic keywords
        if any(keyword in text_lower for keyword in avoid_keywords):
            return True
            
        return False

class TweetAnalysisResult:
    """Represents the result of tweet analysis for spiritual response"""
    
    def __init__(self, selected_tweet: Tweet, detected_mood: str, 
                 bible_verse: Dict, response_text: str, reasoning: str):
        self.selected_tweet = selected_tweet
        self.detected_mood = detected_mood
        self.bible_verse = bible_verse
        self.response_text = response_text
        self.reasoning = reasoning
        
    def __str__(self) -> str:
        return f"Analysis(tweet={self.selected_tweet.id}, mood={self.detected_mood})"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'selected_tweet': self.selected_tweet.to_dict(),
            'detected_mood': self.detected_mood,
            'bible_verse': self.bible_verse,
            'response_text': self.response_text,
            'reasoning': self.reasoning
        }

def create_tweets_from_search_results(search_results: List[Dict]) -> List[Tweet]:
    """Convert search results to Tweet objects"""
    return [Tweet(tweet_data) for tweet_data in search_results]
