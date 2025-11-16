#!/usr/bin/env python3
"""
Test script to test process_mentions() and see the new logging for _has_responded_to_tweet
Can test against Railway PostgreSQL database by setting DATABASE_URL environment variable
"""
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging to see all the debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_process_mentions():
    """Test the process_mentions function with all the new logging"""
    try:
        from interaction_handler import InteractionHandler
        from database import DatabaseManager
        
        logger.info("=" * 80)
        logger.info("🧪 Testing process_mentions() with enhanced logging")
        logger.info("=" * 80)
        
        # Check if DATABASE_URL is set (for Railway PostgreSQL)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            if 'postgresql://' in database_url or 'postgres://' in database_url:
                logger.info(f"✅ Using Railway PostgreSQL database")
                logger.info(f"   Database URL: {database_url[:50]}...")
            else:
                logger.info(f"📝 Using database from DATABASE_URL: {database_url[:50]}...")
        else:
            logger.info(f"📝 No DATABASE_URL set, will use default (SQLite)")
            logger.info(f"   To test against Railway, set DATABASE_URL environment variable")
            logger.info(f"   Example: export DATABASE_URL='postgresql://user:pass@host:port/db'")
        
        logger.info("")
        
        # Initialize handler with dry_run=True to avoid actually posting
        logger.info("📦 Initializing InteractionHandler (dry_run=True)...")
        
        # If DATABASE_URL is set, we need to pass it to DatabaseManager
        # But InteractionHandler creates its own DatabaseManager, so we need to
        # set the environment variable before creating the handler
        handler = InteractionHandler(dry_run=True)
        
        logger.info("")
        logger.info("🚀 Calling process_mentions()...")
        logger.info("   This will trigger _has_responded_to_tweet() for each mention")
        logger.info("   and show all the new debug logging we added")
        logger.info("")
        
        # Process mentions - this will call _has_responded_to_tweet for each mention
        processed_count = handler.process_mentions()
        
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"✅ process_mentions() completed. Processed {processed_count} mentions")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing process_mentions: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_process_mentions()
    sys.exit(0 if success else 1)

