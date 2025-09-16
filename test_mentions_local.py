#!/usr/bin/env python3
"""
Local test script for mentions functionality without API calls
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from interaction_handler import InteractionHandler
from ai_responses import AIResponseGenerator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mention_processing():
    """Test the complete mention processing flow with mock data"""
    
    # Create mock mention data (like what we get from the API)
    import time
    unique_id = str(int(time.time() * 1000))  # Generate unique ID for each test
    mock_mention = {
        'id': unique_id,
        'text': '@InChristAI any words of wisdom today?',
        'author_id': '1476214697598857217',
        'created_at': '2025-09-16T13:13:34.000Z',
        'conversation_id': unique_id,
        'in_reply_to_user_id': '1967203305995595776'
    }
    
    logger.info("🧪 Testing mention processing with mock data...")
    logger.info(f"Mock mention: {mock_mention['text']}")
    
    # Create interaction handler in dry run mode
    handler = InteractionHandler(dry_run=True)
    
    # Test if we should respond to this mention
    should_respond = handler._should_respond_to_mention(mock_mention)
    logger.info(f"Should respond: {should_respond}")
    
    if should_respond:
        # Test the complete processing flow
        logger.info("Processing mention...")
        success = handler._process_single_mention(mock_mention)
        logger.info(f"Processing successful: {success}")
    else:
        logger.info("Would not respond to this mention")

def test_different_mentions():
    """Test with different types of mentions for prompt testing"""
    
    test_mentions = [
        {
            'id': '1111111111111111111',
            'text': '@InChristAI any words of wisdom today?',
            'author_id': '1476214697598857217',
            'created_at': '2025-09-16T13:13:34.000Z',
            'conversation_id': '1111111111111111111',
            'in_reply_to_user_id': '1967203305995595776'
        },
        {
            'id': '2222222222222222222',
            'text': '@InChristAI I need prayer',
            'author_id': '1476214697598857218',
            'created_at': '2025-09-16T13:14:34.000Z',
            'conversation_id': '2222222222222222222',
            'in_reply_to_user_id': '1967203305995595776'
        },
        {
            'id': '3333333333333333333',
            'text': '@InChristAI what does the Bible say about love?',
            'author_id': '1476214697598857219',
            'created_at': '2025-09-16T13:15:34.000Z',
            'conversation_id': '3333333333333333333',
            'in_reply_to_user_id': '1967203305995595776'
        }
    ]
    
    handler = InteractionHandler(dry_run=True)
    
    for i, mention in enumerate(test_mentions, 1):
        logger.info(f"\n=== Test {i}/3 ===")
        logger.info(f"Testing mention: {mention['text']}")
        
        should_respond = handler._should_respond_to_mention(mention)
        if should_respond:
            success = handler._process_single_mention(mention)
            logger.info(f"Response generated: {success}")
        else:
            logger.info("Would not respond to this mention")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "multi":
        test_different_mentions()
    else:
        test_mention_processing()
        print("\n💡 Tip: Run 'python3 test_mentions_local.py multi' to test multiple mention types")
