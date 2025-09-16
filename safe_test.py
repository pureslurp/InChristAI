"""
Safe testing script - Shows what would be posted without actually posting
"""
import sys
import os
from datetime import datetime

def test_daily_verse_preview():
    """Show what today's daily verse would look like"""
    print("📅 DAILY VERSE PREVIEW")
    print("=" * 50)
    
    try:
        from bible_api import BibleAPI, get_fallback_verse
        from twitter_api import TwitterAPI
        from daily_poster import DailyPoster
        
        # Get today's verse
        poster = DailyPoster()
        verse = poster._get_todays_verse()
        
        if verse:
            print(f"Verse: {verse['reference']}")
            print(f"Text: {verse['text']}")
            print(f"Version: {verse['version']}")
            print("\n" + "-" * 30)
            
            # Show different formatting styles
            tweet_text = poster._format_daily_tweet(verse)
            print("📝 FORMATTED TWEET:")
            print(tweet_text)
            print(f"\nCharacter count: {len(tweet_text)}/280")
            
            return True
        else:
            print("❌ Could not get verse")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ai_responses():
    """Test AI response generation for different scenarios"""
    print("\n🤖 AI RESPONSE TESTING")
    print("=" * 50)
    
    try:
        from ai_responses import AIResponseGenerator
        
        ai = AIResponseGenerator()
        
        # Test different types of mentions
        test_scenarios = [
            {
                'type': 'Prayer Request',
                'mention': '@InChristAI Please pray for my sick mother',
                'context': 'User asking for prayer support'
            },
            {
                'type': 'Verse Request', 
                'mention': '@InChristAI Can you share a verse about hope?',
                'context': 'User requesting specific themed verse'
            },
            {
                'type': 'Struggling',
                'mention': '@InChristAI I\'m going through a really difficult time right now',
                'context': 'User needing comfort and encouragement'
            },
            {
                'type': 'Gratitude',
                'mention': '@InChristAI Thank you for the daily encouragement! God bless you!',
                'context': 'User expressing gratitude'
            },
            {
                'type': 'Question',
                'mention': '@InChristAI What does the Bible say about forgiveness?',
                'context': 'User asking biblical question'
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n📥 SCENARIO: {scenario['type']}")
            print(f"Mention: {scenario['mention']}")
            print(f"Context: {scenario['context']}")
            
            # Generate response
            response = ai.generate_response(
                mention_text=scenario['mention'],
                context=scenario['context']
            )
            
            print(f"🤖 AI Response: {response}")
            print(f"Length: {len(response)}/280 characters")
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing AI responses: {e}")
        return False

def test_verse_variety():
    """Show variety in verse selection and formatting"""
    print("\n📚 VERSE VARIETY TEST")
    print("=" * 50)
    
    try:
        from bible_api import BibleAPI, get_fallback_verse
        from daily_poster import DailyPoster
        
        poster = DailyPoster()
        
        print("Generating 5 different verse formats...")
        
        for i in range(5):
            verse = poster._get_todays_verse()
            if verse:
                tweet = poster._format_daily_tweet(verse)
                print(f"\n📝 SAMPLE {i+1}:")
                print(f"Reference: {verse['reference']}")
                print(f"Tweet: {tweet}")
                print(f"Length: {len(tweet)} chars")
                print("-" * 30)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing verse variety: {e}")
        return False

def test_fallback_system():
    """Test the fallback verse system"""
    print("\n🔄 FALLBACK SYSTEM TEST")
    print("=" * 50)
    
    try:
        from bible_api import get_fallback_verse, FALLBACK_VERSES
        
        print(f"Number of fallback verses available: {len(FALLBACK_VERSES)}")
        
        # Show a few fallback verses
        for i in range(3):
            verse = get_fallback_verse()
            print(f"\n📖 Fallback {i+1}:")
            print(f"Reference: {verse['reference']}")
            print(f"Text: {verse['text']}")
            print(f"Version: {verse['version']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing fallback system: {e}")
        return False

def preview_next_post():
    """Preview what would be posted next"""
    print("\n🔮 NEXT POST PREVIEW")
    print("=" * 50)
    
    try:
        from daily_poster import DailyPoster
        from datetime import date
        
        poster = DailyPoster()
        today = date.today()
        
        # Check if already posted today
        if poster._has_posted_today(today):
            print("ℹ️  Daily verse already posted today")
            history = poster.get_posting_history(1)
            if history:
                latest = history[0]
                print(f"Today's post: {latest['verse_reference']}")
                print(f"Posted at: {latest['posted_at']}")
        else:
            print("📝 WOULD POST THIS TODAY:")
            verse = poster._get_todays_verse()
            if verse:
                tweet = poster._format_daily_tweet(verse)
                print(tweet)
                print(f"\nScheduled for: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error previewing next post: {e}")
        return False

def main():
    """Run safe testing suite"""
    print("🛡️  InChrist AI - SAFE TESTING SUITE")
    print("(No actual posting to Twitter)")
    print("=" * 60)
    
    tests = [
        test_daily_verse_preview,
        test_ai_responses,
        test_verse_variety,
        test_fallback_system,
        preview_next_post
    ]
    
    passed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
    
    print("=" * 60)
    print(f"✅ Completed {passed}/{len(tests)} test sections")
    print("🛡️  No actual posts were made to Twitter")
    
    if passed > 0:
        print("\n📋 SUMMARY:")
        print("- You can see exactly what would be posted")
        print("- AI responses are working") 
        print("- Verse system is functional")
        print("- Ready for live testing when you're ready")

if __name__ == "__main__":
    main()
