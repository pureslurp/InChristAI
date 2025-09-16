"""
Setup script for InChrist AI Twitter Bot
"""
import os
import shutil
import sys

def setup_bot():
    """Initial setup for the bot"""
    print("Setting up InChrist AI Twitter Bot...")
    
    # Create config.py from template
    if not os.path.exists('config.py'):
        if os.path.exists('config_example.py'):
            shutil.copy('config_example.py', 'config.py')
            print("✅ Created config.py from template")
            print("⚠️  Please edit config.py with your API keys and settings")
        else:
            print("❌ config_example.py not found")
            return False
    else:
        print("ℹ️  config.py already exists")
    
    # Create logs directory
    if not os.path.exists('logs'):
        os.makedirs('logs')
        print("✅ Created logs directory")
    
    # Check if required packages are installed
    try:
        import tweepy
        import openai
        import requests
        import schedule
        import sqlalchemy
        print("✅ All required packages are available")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit config.py with your API keys")
    print("2. Run: python main.py help")
    print("3. Test with: python main.py status")
    print("4. Start the bot: python main.py start")
    
    return True

def check_config():
    """Check if configuration is properly set up"""
    try:
        import config
        
        required_vars = [
            'TWITTER_API_KEY',
            'TWITTER_API_SECRET', 
            'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET',
            'TWITTER_BEARER_TOKEN',
            'OPENAI_API_KEY',
            'BOT_USERNAME'
        ]
        
        missing_vars = []
        for var in required_vars:
            value = getattr(config, var, None)
            if not value or value == "your_api_key_here" or value == "your_bot_username":
                missing_vars.append(var)
        
        if missing_vars:
            print("❌ Configuration incomplete. Missing or default values for:")
            for var in missing_vars:
                print(f"   - {var}")
            return False
        
        print("✅ Configuration looks good!")
        return True
        
    except ImportError:
        print("❌ config.py not found. Run setup first.")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_config()
    else:
        setup_bot()
