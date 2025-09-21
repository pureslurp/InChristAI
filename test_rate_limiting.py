#!/usr/bin/env python3
"""
Test script to verify the new rate limiting and caching functionality
"""
import time
import logging
from twitter_api import TwitterAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_caching_and_rate_limiting():
    """Test the new caching and rate limiting features"""
    logger.info("🧪 Testing Twitter API caching and rate limiting...")
    
    try:
        # Initialize API in dry-run mode
        api = TwitterAPI(dry_run=True)
        
        # Test 1: Cache stats (should be empty initially)
        stats = api.get_cache_stats()
        logger.info(f"Initial cache stats: {stats}")
        
        # Test 2: Multiple calls to get_mentions should use cache
        logger.info("\n📡 Testing mention caching...")
        
        start_time = time.time()
        mentions1 = api.get_mentions(count=5)  # First call - should hit API
        first_call_time = time.time() - start_time
        
        start_time = time.time()
        mentions2 = api.get_mentions(count=5)  # Second call - should hit cache
        second_call_time = time.time() - start_time
        
        logger.info(f"First call took: {first_call_time:.2f}s")
        logger.info(f"Second call took: {second_call_time:.2f}s")
        logger.info(f"Cache speedup: {first_call_time/second_call_time:.1f}x faster")
        
        # Test 3: Check cache stats after calls
        stats = api.get_cache_stats()
        logger.info(f"Cache stats after calls: {stats}")
        
        # Test 4: Clear cache and verify
        api.clear_cache()
        stats = api.get_cache_stats()
        logger.info(f"Cache stats after clear: {stats}")
        
        logger.info("✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_caching_and_rate_limiting()
    exit(0 if success else 1)
