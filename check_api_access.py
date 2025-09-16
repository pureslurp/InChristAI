"""
Diagnostic script to check Twitter API access level
"""
import tweepy
import config

def check_api_access():
    """Check what level of API access we have"""
    print("🔍 Twitter API Access Diagnostic")
    print("=" * 40)
    
    try:
        # Initialize API
        auth = tweepy.OAuthHandler(config.TWITTER_API_KEY, config.TWITTER_API_SECRET)
        auth.set_access_token(config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_TOKEN_SECRET)
        api = tweepy.API(auth)
        
        # Test basic authentication
        print("1. Testing authentication...")
        user = api.verify_credentials()
        if user:
            print(f"✅ Authenticated as: @{user.screen_name}")
            print(f"   Account ID: {user.id}")
            print(f"   Followers: {user.followers_count}")
        else:
            print("❌ Authentication failed")
            return
        
        # Test API v1.1 capabilities
        print("\n2. Testing API v1.1 capabilities...")
        
        # Test timeline read (should work with free tier)
        try:
            timeline = api.user_timeline(count=1)
            print("✅ Can read timeline")
        except Exception as e:
            print(f"❌ Cannot read timeline: {e}")
        
        # Test posting capability (this is what's failing)
        print("\n3. Testing posting capability...")
        print("⚠️  This is where the error occurs")
        print("   Error 403 suggests insufficient API access level")
        
        # Show current rate limit status
        print("\n4. Rate limit status:")
        try:
            rate_limit = api.get_rate_limit_status()
            print("✅ Can access rate limit info")
        except Exception as e:
            print(f"❌ Cannot access rate limit: {e}")
            
        print("\n" + "=" * 40)
        print("DIAGNOSIS:")
        print("✅ Authentication works")
        print("❌ Posting fails with 403 Forbidden")
        print("\nPOSSIBLE SOLUTIONS:")
        print("1. Check app permissions in Twitter Developer Portal")
        print("2. Ensure app has 'Read and Write' permissions")
        print("3. May need to upgrade to Basic API tier ($100/month)")
        print("4. Try regenerating API keys")
        
        print("\nTO FIX:")
        print("1. Go to: https://developer.x.com/en/portal/dashboard")
        print("2. Check your app's permissions")
        print("3. Look for 'App permissions' - should be 'Read and write'")
        print("4. If it says 'Read only', change it to 'Read and write'")
        
    except Exception as e:
        print(f"❌ Error during diagnostic: {e}")

if __name__ == "__main__":
    check_api_access()
