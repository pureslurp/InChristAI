#!/usr/bin/env python3
"""
Check current X API usage and rate limit status
"""
import requests
import logging
from datetime import datetime

# Use cloud config if available, fallback to local config
try:
    import config_cloud as config
except ImportError:
    import config

def check_api_usage():
    """Check current API usage using the official usage API"""
    print("🔍 X API Usage Checker")
    print("=" * 50)
    
    try:
        # Use the official usage API endpoint
        usage_url = "https://api.x.com/2/usage/tweets"
        
        headers = {
            "Authorization": f"Bearer {config.TWITTER_BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
        
        print("📡 Checking usage via official usage API...")
        usage_response = requests.get(usage_url, headers=headers)
        
        print(f"📊 Usage API Response Status: {usage_response.status_code}")
        
        if usage_response.status_code == 200:
            usage_data = usage_response.json()
            print(f"📈 Official Usage Data: {usage_data}")
            
            # Parse the usage data if available
            if 'data' in usage_data:
                data = usage_data['data']
                print(f"\n📊 Usage Summary from Official API:")
                
                # Look for usage metrics
                for key, value in data.items():
                    print(f"  {key}: {value}")
                    
                # Check if we're near limits
                if 'usage' in str(data).lower():
                    print("✅ Official usage data retrieved successfully")
                else:
                    print("⚠️  Usage data format may have changed")
            
            # Also get rate limit headers from this call
            usage_headers = {}
            for header_name, header_value in usage_response.headers.items():
                if 'rate' in header_name.lower() or 'limit' in header_name.lower():
                    usage_headers[header_name] = header_value
            
            if usage_headers:
                print(f"\n🔢 Rate Limit Headers from Usage API:")
                for key, value in usage_headers.items():
                    print(f"  {key}: {value}")
            
        else:
            print(f"❌ Usage API failed ({usage_response.status_code}): {usage_response.text}")
            print("🔄 Falling back to rate limit headers method...")
            
            # Fallback to the old method
            fallback_url = f"https://api.x.com/2/users/{config.TWITTER_USER_ID}/mentions"
            params = {
                "max_results": 5,  # Minimal request
                "tweet.fields": "created_at"
            }
            
            response = requests.get(fallback_url, headers=headers, params=params)
            print(f"📊 Fallback Response Status: {response.status_code}")
            
            # Extract rate limit headers from fallback
            rate_limit_info = {}
            for header_name, header_value in response.headers.items():
                if 'rate' in header_name.lower() or 'limit' in header_name.lower():
                    rate_limit_info[header_name] = header_value
            
            if rate_limit_info:
                print("\n🔢 Fallback Rate Limit Information:")
                for key, value in rate_limit_info.items():
                    print(f"  {key}: {value}")
                
                # Extract key metrics
                remaining = rate_limit_info.get('x-rate-limit-remaining', 'unknown')
                limit = rate_limit_info.get('x-rate-limit-limit', 'unknown')
                reset_time = rate_limit_info.get('x-rate-limit-reset', 'unknown')
                
                print(f"\n📈 Fallback Usage Summary:")
                print(f"  Calls Remaining: {remaining}")
                print(f"  Total Limit: {limit}")
                
                if reset_time != 'unknown':
                    try:
                        reset_datetime = datetime.fromtimestamp(int(reset_time))
                        print(f"  Resets At: {reset_datetime}")
                    except:
                        print(f"  Reset Time: {reset_time}")
                
                # Calculate usage
                if remaining != 'unknown' and limit != 'unknown':
                    try:
                        used = int(limit) - int(remaining)
                        usage_percent = (used / int(limit)) * 100
                        print(f"  Calls Used: {used} ({usage_percent:.1f}%)")
                        
                        if usage_percent > 80:
                            print("⚠️  WARNING: High API usage!")
                        elif usage_percent > 50:
                            print("⚡ CAUTION: Moderate API usage")
                        else:
                            print("✅ GOOD: Low API usage")
                            
                    except:
                        print("  Could not calculate usage percentage")
            else:
                print("❌ No rate limit headers found in fallback response")
                
            if response.status_code == 429:
                print("\n🚫 RATE LIMIT EXCEEDED!")
                print("   Your API calls are currently blocked")
                print("   Wait for the reset time or reduce API frequency")
            elif response.status_code == 200:
                print("\n✅ Fallback API Access OK")
            else:
                print(f"\n⚠️  Fallback API Response: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        
        # Final status check
        final_status = usage_response.status_code if 'usage_response' in locals() else response.status_code
        if final_status == 200:
            print("\n✅ Overall API Status: OK")
        elif final_status == 429:
            print("\n🚫 Overall API Status: RATE LIMITED")
        else:
            print(f"\n⚠️  Overall API Status: {final_status}")
            
    except Exception as e:
        print(f"❌ Error checking API usage: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("💡 Recommendations:")
    print("   - Current bot schedule: 2 API calls/day (very conservative)")
    print("   - Monitor logs for '💰 API CALL MADE' messages")
    print("   - Monthly limit: 100 calls (X API Free tier)")
    
    return True

if __name__ == "__main__":
    check_api_usage()
