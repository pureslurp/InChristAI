#!/usr/bin/env python3
"""
Test script to verify database functionality with both SQLite and PostgreSQL
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database():
    """Test database functionality"""
    print("🧪 Testing database functionality...")
    
    try:
        from database import DatabaseManager
        
        # Test 1: SQLite (default)
        print("\n📝 Test 1: SQLite Database")
        db_sqlite = DatabaseManager("sqlite:///test_sqlite.db")
        db_sqlite.init_tables()
        
        # Test insert
        result = db_sqlite.execute_update(
            "INSERT INTO interactions (tweet_id, user_id, mention_text, created_at, interaction_type) VALUES (%s, %s, %s, %s, %s)" if db_sqlite.is_postgres else
            "INSERT INTO interactions (tweet_id, user_id, mention_text, created_at, interaction_type) VALUES (?, ?, ?, ?, ?)",
            ("test123", "user456", "Test mention", "2024-01-01T12:00:00Z", "test")
        )
        print(f"✅ SQLite insert successful: {result} rows affected")
        
        # Test query
        results = db_sqlite.execute_query(
            "SELECT * FROM interactions WHERE tweet_id = %s" if db_sqlite.is_postgres else
            "SELECT * FROM interactions WHERE tweet_id = ?",
            ("test123",)
        )
        print(f"✅ SQLite query successful: {len(results)} results")
        
        # Test stats
        stats = db_sqlite.get_stats()
        print(f"✅ SQLite stats: {stats}")
        
        # Clean up test database
        os.remove("test_sqlite.db")
        print("✅ SQLite test completed successfully")
        
        # Test 2: PostgreSQL (if DATABASE_URL is set)
        if os.getenv('DATABASE_URL') and 'postgresql://' in os.getenv('DATABASE_URL'):
            print("\n📝 Test 2: PostgreSQL Database")
            db_postgres = DatabaseManager()
            db_postgres.init_tables()
            
            # Test insert
            result = db_postgres.execute_update(
                "INSERT INTO interactions (tweet_id, user_id, mention_text, created_at, interaction_type) VALUES (%s, %s, %s, %s, %s)",
                ("test456", "user789", "Test PostgreSQL mention", "2024-01-01T12:00:00Z", "test")
            )
            print(f"✅ PostgreSQL insert successful: {result} rows affected")
            
            # Test query
            results = db_postgres.execute_query(
                "SELECT * FROM interactions WHERE tweet_id = %s",
                ("test456",)
            )
            print(f"✅ PostgreSQL query successful: {len(results)} results")
            
            # Test stats
            stats = db_postgres.get_stats()
            print(f"✅ PostgreSQL stats: {stats}")
            
            # Clean up test data
            db_postgres.execute_update(
                "DELETE FROM interactions WHERE tweet_id = %s",
                ("test456",)
            )
            print("✅ PostgreSQL test completed successfully")
        else:
            print("\n📝 Test 2: PostgreSQL Database - SKIPPED (no DATABASE_URL with postgresql://)")
        
        print("\n🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_interaction_handler():
    """Test interaction handler with new database"""
    print("\n🧪 Testing InteractionHandler with new database...")
    
    try:
        from interaction_handler import InteractionHandler
        
        # Create handler (will use default database)
        handler = InteractionHandler(dry_run=True)
        
        # Test stats
        stats = handler.get_interaction_stats()
        print(f"✅ InteractionHandler stats: {stats}")
        
        # Test cleanup
        cleaned = handler.cleanup_old_data(days=30)
        print(f"✅ InteractionHandler cleanup: {cleaned} records cleaned")
        
        print("✅ InteractionHandler test completed successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ InteractionHandler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting database migration tests...")
    
    # Check environment
    database_url = os.getenv('DATABASE_URL', 'Not set')
    print(f"📊 DATABASE_URL: {database_url}")
    
    success1 = test_database()
    success2 = test_interaction_handler()
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! Database migration is ready!")
        print("\n📋 Next steps:")
        print("1. Add PostgreSQL service in Railway dashboard")
        print("2. Set DATABASE_URL environment variable")
        print("3. Deploy your bot")
        print("4. Your data will now persist across deployments! 🎉")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
