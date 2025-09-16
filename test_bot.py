"""
Test script for InChrist AI Bot components
"""
import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import tweepy
        print("✅ tweepy imported successfully")
    except ImportError:
        print("❌ tweepy import failed")
        return False
    
    try:
        import openai
        print("✅ openai imported successfully")
    except ImportError:
        print("❌ openai import failed")
        return False
    
    try:
        import requests
        print("✅ requests imported successfully")
    except ImportError:
        print("❌ requests import failed")
        return False
    
    try:
        import schedule
        print("✅ schedule imported successfully")
    except ImportError:
        print("❌ schedule import failed")
        return False
    
    return True

def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    
    try:
        import config
        print("✅ config.py loaded successfully")
        
        # Check for required variables
        required_vars = ['TWITTER_API_KEY', 'OPENAI_API_KEY', 'BOT_USERNAME']
        for var in required_vars:
            if hasattr(config, var):
                value = getattr(config, var)
                if value and value != "your_api_key_here":
                    print(f"✅ {var} is set")
                else:
                    print(f"⚠️  {var} needs to be configured")
            else:
                print(f"❌ {var} not found in config")
        
        return True
        
    except ImportError:
        print("❌ config.py not found - run python setup.py first")
        return False

def test_modules():
    """Test our custom modules"""
    print("\nTesting custom modules...")
    
    try:
        from bible_api import BibleAPI, get_fallback_verse
        print("✅ bible_api module imported")
        
        # Test fallback verse
        verse = get_fallback_verse()
        if verse and 'text' in verse:
            print(f"✅ Fallback verse working: {verse['reference']}")
        else:
            print("❌ Fallback verse failed")
            
    except Exception as e:
        print(f"❌ bible_api test failed: {e}")
        return False
    
    try:
        from twitter_api import TwitterAPI
        print("✅ twitter_api module imported")
    except Exception as e:
        print(f"❌ twitter_api test failed: {e}")
        return False
    
    try:
        from ai_responses import AIResponseGenerator
        print("✅ ai_responses module imported")
    except Exception as e:
        print(f"❌ ai_responses test failed: {e}")
        return False
    
    try:
        from daily_poster import DailyPoster
        print("✅ daily_poster module imported")
    except Exception as e:
        print(f"❌ daily_poster test failed: {e}")
        return False
    
    try:
        from interaction_handler import InteractionHandler
        print("✅ interaction_handler module imported")
    except Exception as e:
        print(f"❌ interaction_handler test failed: {e}")
        return False
    
    return True

def test_bible_api():
    """Test Bible API functionality"""
    print("\nTesting Bible API...")
    
    try:
        from bible_api import BibleAPI, get_fallback_verse
        
        # Test fallback verses (always works)
        verse = get_fallback_verse()
        print(f"✅ Fallback verse: {verse['reference']} - {verse['text'][:50]}...")
        
        # Test actual API (may fail if no API key)
        bible_api = BibleAPI()
        try:
            verse = bible_api.get_random_verse()
            if verse:
                print(f"✅ Bible API working: {verse['reference']}")
            else:
                print("⚠️  Bible API returned no verse (check API key)")
        except Exception as e:
            print(f"⚠️  Bible API failed (using fallbacks): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bible API test failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\nTesting database...")
    
    try:
        from interaction_handler import InteractionHandler
        
        handler = InteractionHandler()
        print("✅ Database initialized successfully")
        
        # Test getting stats (should work even with empty database)
        stats = handler.get_interaction_stats()
        print(f"✅ Database stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("InChrist AI Bot - Component Tests")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_config,
        test_modules,
        test_bible_api,
        test_database
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready to run.")
        print("\nNext steps:")
        print("1. Verify your API keys in config.py")
        print("2. Run: python main.py status")
        print("3. Test posting: python main.py post_verse")
        print("4. Start the bot: python main.py start")
    else:
        print("⚠️  Some tests failed. Please fix the issues before running the bot.")
        print("\nTroubleshooting:")
        print("- Run: python setup.py")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Configure API keys in config.py")

if __name__ == "__main__":
    main()
