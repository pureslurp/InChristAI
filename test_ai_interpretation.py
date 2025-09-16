"""
Test script to specifically show AI interpretation of verses
"""
from daily_poster import DailyPoster
from ai_responses import AIResponseGenerator
from bible_api import BibleAPI, get_fallback_verse

def test_ai_interpretation():
    """Test AI interpretation of verses"""
    print("🤖 AI VERSE INTERPRETATION TEST")
    print("=" * 50)
    
    try:
        poster = DailyPoster(dry_run=True)
        ai_gen = AIResponseGenerator()
        
        # Get a verse
        verse = poster._get_todays_verse()
        
        if not verse:
            print("❌ Could not get verse")
            return
        
        print(f"📖 VERSE:")
        print(f"Reference: {verse['reference']}")
        print(f"Text: {verse['text']}")
        print(f"Version: {verse['version']}")
        
        print(f"\n🤖 AI INTERPRETATION:")
        print("-" * 30)
        
        # Generate AI interpretation
        ai_interpretation = ai_gen.generate_daily_post_text(verse)
        print(f"AI Says: {ai_interpretation}")
        
        print(f"\n📝 FULL TWEET WITH AI INTERPRETATION:")
        print("-" * 50)
        
        # Force the reflection style to see AI interpretation
        tweet_with_ai = poster._format_daily_tweet(verse, force_style='verse_with_reflection')
        print(tweet_with_ai)
        print(f"\nCharacter count: {len(tweet_with_ai)}/280")
        
        print(f"\n📋 COMPARISON - Simple intro vs AI:")
        print("-" * 50)
        
        # Show simple intro version
        tweet_simple = poster._format_daily_tweet(verse, force_style='verse_with_intro')
        print("SIMPLE INTRO:")
        print(tweet_simple)
        
        print("\nAI INTERPRETATION:")
        print(tweet_with_ai)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_multiple_interpretations():
    """Test AI interpretations of different verse themes"""
    print("\n🎯 MULTIPLE AI INTERPRETATIONS TEST")
    print("=" * 50)
    
    try:
        bible_api = BibleAPI()
        ai_gen = AIResponseGenerator()
        poster = DailyPoster(dry_run=True)
        
        # Test with different verses
        test_verses = [
            get_fallback_verse(),  # Will be random from fallbacks
            get_fallback_verse(),
            get_fallback_verse()
        ]
        
        for i, verse in enumerate(test_verses, 1):
            print(f"\n📖 VERSE {i}: {verse['reference']}")
            print(f"Text: {verse['text'][:100]}...")
            
            # Generate AI interpretation
            ai_text = ai_gen.generate_daily_post_text(verse)
            print(f"🤖 AI Interpretation: {ai_text}")
            
            # Show full tweet
            tweet = poster._format_daily_tweet(verse, force_style='verse_with_reflection')
            print(f"📝 Full Tweet:\n{tweet}")
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing AI interpretation functionality...")
    print("This will show you the AI-generated reflections on verses.\n")
    
    test_ai_interpretation()
    test_multiple_interpretations()
    
    print("\n✅ Now try running: python main.py post_verse --dry-run")
    print("   (It should use AI interpretation more often now)")
