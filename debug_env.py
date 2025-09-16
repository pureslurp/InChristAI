#!/usr/bin/env python3
"""
Debug script to check environment variables in Railway
"""
import os

print("=== Environment Variables Debug ===")
print(f"CLOUD_DEPLOYMENT: {os.getenv('CLOUD_DEPLOYMENT')}")
print(f"PORT: {os.getenv('PORT')}")
print(f"OPENAI_API_KEY present: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"TWITTER_API_KEY present: {bool(os.getenv('TWITTER_API_KEY'))}")
print(f"BOT_USERNAME: {os.getenv('BOT_USERNAME')}")

# Try importing config
try:
    if os.getenv('CLOUD_DEPLOYMENT') or os.getenv('PORT'):
        print("Attempting to import config_cloud...")
        import config_cloud as config
        print("✅ Successfully imported config_cloud")
        print(f"OpenAI API Key from config: {bool(getattr(config, 'OPENAI_API_KEY', None))}")
    else:
        print("Attempting to import config...")
        import config
        print("✅ Successfully imported config")
except Exception as e:
    print(f"❌ Error importing config: {e}")

print("=== End Debug ===")
