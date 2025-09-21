"""
AI-powered response generation for Twitter interactions
"""
import logging
from typing import Dict, List, Optional
import re
# Use cloud config if available, fallback to local config
try:
    import config_cloud as config
except ImportError:
    import config
from bible_api import BibleAPI
from tweet_models import Tweet, TweetAnalysisResult, create_tweets_from_search_results

logger = logging.getLogger(__name__)

class AIResponseGenerator:
    def __init__(self):
        # Debug config loading
        logger.info(f"Loading AI config - API key present: {bool(getattr(config, 'OPENAI_API_KEY', None))}")
        logger.info(f"AI Model: {getattr(config, 'AI_MODEL', 'NOT_SET')}")
        
        # Validate API key
        api_key = getattr(config, 'OPENAI_API_KEY', None)
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in configuration")
        
        # Initialize OpenAI client with error handling (v1.0+ style)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
            
        self.model = getattr(config, 'AI_MODEL', 'gpt-4o-mini')
        self.temperature = getattr(config, 'AI_TEMPERATURE', 0.7)
        self.max_response_length = getattr(config, 'MAX_RESPONSE_LENGTH', 180)
        self.bible_api = BibleAPI()
        
        # System prompt for the AI assistant
        self.system_prompt = """You are InChrist AI, a compassionate Christian companion on Twitter dedicated to sharing God's love and encouragement.

IDENTITY & PERSONALITY:
- Name: InChrist AI
- Mission: To spread God's word by helping people understand the Bible and applying it to their lives.
- Personality: Warm, gentle, encouraging, patient, and joyful
- Voice: Authentic, conversational, never robotic or overly formal
- Heart: Genuinely cares about each person who reaches out

CORE VALUES & BELIEFS:
- Jesus Christ is Lord and Savior
- The Bible is God's Word and source of truth
- Every person is loved by God and has value
- Grace, mercy, and forgiveness are freely given
- Prayer is powerful and important
- Community and fellowship matter
- Hope is always available in Christ

RESPONSE GUIDELINES:
1. Always respond with Christ-like love, kindness, and compassion
2. Keep responses under 280 characters for Twitter
3. Share relevant Bible verses when appropriate
4. Be encouraging and uplifting in every interaction
5. Avoid controversial theological debates or denominational arguments
6. Focus on core Christian values: love, hope, faith, forgiveness, grace
7. Use simple, accessible language that everyone can understand
8. Include relevant emojis when they enhance the message (🙏💕✨🌟)
9. Never be preachy, judgmental, or condescending
10. When someone is hurting, offer genuine comfort, prayer, and hope

SPECIAL SITUATIONS:
- Prayer requests: Always offer to pray, include comforting verses
- Questions about faith: Answer with love and biblical wisdom
- Difficult times: Point to God's faithfulness and presence
- Celebration: Rejoice with them and give glory to God
- Doubt/struggles: Offer hope without dismissing their feelings

TONE EXAMPLES:
- "I'm praying for you 🙏"
- "God loves you so much 💕"
- "Here's a verse that might encourage your heart..."
- "What a blessing! Praising God with you 🙌"
- "You're not alone in this - God is with you ✨"

Remember: You represent Christ's love in every interaction. Be authentic, caring, and always point people toward God's hope and love."""

    def generate_response(self, mention_text: str, user_info: Dict = None, context: str = "") -> Optional[str]:
        """Generate an AI response to a mention or interaction"""
        try:
            # Analyze the mention to understand intent
            intent = self._analyze_intent(mention_text)
            
            # Build the prompt based on intent
            prompt = self._build_prompt(mention_text, intent, user_info, context)
            
            # Log the complete prompt being sent to AI
            logger.info("=" * 50)
            logger.info("🤖 AI PROMPT DEBUG:")
            logger.info("-" * 30)
            logger.info("USER PROMPT:")
            logger.info(prompt)
            logger.info("=" * 50)
            
            # Generate response using OpenAI (v1.0+ format)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=100  # Keep responses concise for Twitter
            )
            
            generated_text = response.choices[0].message.content.strip()
            
            # Post-process the response
            formatted_response = self._format_response(generated_text)
            
            logger.info(f"Generated response: {formatted_response}")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            return self._get_fallback_response(mention_text)

    def _analyze_intent(self, text: str) -> str:
        """Analyze the intent of the mention"""
        text_lower = text.lower()
        
        # Prayer request patterns
        prayer_keywords = ['pray', 'prayer', 'prayers', 'praying', 'please pray', 'need prayer']
        if any(keyword in text_lower for keyword in prayer_keywords):
            return 'prayer_request'
        
        # Verse request patterns
        verse_keywords = ['verse', 'bible', 'scripture', 'word', 'passage']
        if any(keyword in text_lower for keyword in verse_keywords):
            return 'verse_request'
        
        # Encouragement/comfort patterns
        comfort_keywords = ['struggling', 'difficult', 'hard time', 'depressed', 'anxious', 'worried', 'scared', 'hurt', 'pain', 'lost', 'confused']
        if any(keyword in text_lower for keyword in comfort_keywords):
            return 'comfort_needed'
        
        # Gratitude/praise patterns
        praise_keywords = ['thank', 'grateful', 'blessed', 'praise', 'amazing', 'wonderful', 'glory']
        if any(keyword in text_lower for keyword in praise_keywords):
            return 'gratitude'
        
        # Question patterns
        if '?' in text or text_lower.startswith(('what', 'how', 'why', 'when', 'where', 'who')):
            return 'question'
        
        return 'general'

    def _build_prompt(self, mention_text: str, intent: str, user_info: Dict = None, context: str = "") -> str:
        """Build a tailored prompt based on the intent and context"""
        base_prompt = f"Someone mentioned you on Twitter saying: '{mention_text}'"
        
        # Skip user info since we don't need username for replies
        
        if context:
            base_prompt += f"\nContext: {context}"
            
            # If the context includes an original tweet, emphasize its importance
            if "They are replying to this original tweet:" in context:
                base_prompt += "\n\nIMPORTANT: The person is responding to a specific tweet. Use the original tweet content to understand what they're referring to when they say 'this' or similar references. Tailor your response to address their feelings about the original tweet's content."
        
        # Add intent-specific instructions
        if intent == 'prayer_request':
            base_prompt += "\n\nThis appears to be a prayer request. Respond with compassion, offer to pray for them, and perhaps include a comforting Bible verse."
        
        elif intent == 'verse_request':
            base_prompt += "\n\nThey're asking for a Bible verse. Provide an encouraging verse that fits their situation."
        
        elif intent == 'comfort_needed':
            base_prompt += "\n\nThis person seems to be going through a difficult time. Offer comfort, hope, and biblical encouragement."
        
        elif intent == 'gratitude':
            base_prompt += "\n\nThey're expressing gratitude or praise. Celebrate with them and perhaps add a verse about thanksgiving."
        
        elif intent == 'question':
            base_prompt += "\n\nThey have a question. Answer helpfully while staying true to Christian values."
        
        else:
            base_prompt += "\n\nRespond in a friendly, encouraging way that reflects Christian love."
        
        base_prompt += "\n\nGenerate a tweet-length response (under 280 characters) that is warm, genuine, and helpful. Do NOT include @username mentions - Twitter will handle reply tagging automatically."
        base_prompt += "\n\nIMPORTANT: If the person is being combative, rude, argumentative, or if responding would seem annoying/intrusive, simply respond with 'NO_REPLY' instead of generating a response. Only reply when it would genuinely be helpful and welcomed."
        base_prompt += "\n\nExamples of when to use NO_REPLY:"
        base_prompt += "\n- Hostile language or personal attacks"
        base_prompt += "\n- Mocking religion or faith"
        base_prompt += "\n- Obvious spam or promotional content"
        base_prompt += "\n- Private conversations between others where you weren't specifically invited"
        base_prompt += "\n- Content that seems designed to provoke arguments"
        base_prompt += "\n- When the person seems annoyed by bot responses"
        
        return base_prompt

    def _format_response(self, response: str) -> str:
        """Format and validate the AI response"""
        # Remove quotes if the AI wrapped the response in them
        response = response.strip('"\'')
        
        # Ensure it fits Twitter's character limit
        if len(response) > self.max_response_length:
            # Try to truncate at a sentence boundary
            sentences = response.split('. ')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + '. ') <= self.max_response_length - 3:
                    truncated += sentence + '. '
                else:
                    break
            
            if truncated:
                response = truncated.rstrip('. ') + '...'
            else:
                response = response[:self.max_response_length-3] + '...'
        
        return response

    def _get_fallback_response(self, mention_text: str) -> str:
        """Provide a fallback response when AI generation fails"""
        intent = self._analyze_intent(mention_text)
        
        fallback_responses = {
            'prayer_request': "🙏 I'm praying for you! 'And the peace of God, which transcends all understanding, will guard your hearts and your minds in Christ Jesus.' - Philippians 4:7",
            'verse_request': "'For I know the plans I have for you,' declares the Lord, 'plans to prosper you and not to harm you, to give you hope and a future.' - Jeremiah 29:11 ✨",
            'comfort_needed': "💙 Remember that you're loved and not alone. 'The Lord is close to the brokenhearted and saves those who are crushed in spirit.' - Psalm 34:18",
            'gratitude': "🙌 Praise God! 'Give thanks to the Lord, for he is good; his love endures forever.' - Psalm 107:1",
            'question': "Thank you for reaching out! May God bless you and guide you. 'Trust in the Lord with all your heart.' - Proverbs 3:5 💕",
            'general': "God bless you! 🙏 'Be strong and courageous. Do not be afraid; do not be discouraged, for the Lord your God will be with you wherever you go.' - Joshua 1:9"
        }
        
        return fallback_responses.get(intent, fallback_responses['general'])

    def get_verse_for_topic(self, topic: str) -> Optional[Dict]:
        """Get a relevant Bible verse for a specific topic"""
        topic_keywords = {
            'fear': 'fear anxiety worried',
            'hope': 'hope future plans',
            'love': 'love compassion kindness',
            'strength': 'strength courage power',
            'peace': 'peace calm rest',
            'forgiveness': 'forgiveness mercy grace',
            'faith': 'faith trust believe',
            'comfort': 'comfort help support',
            'joy': 'joy happiness rejoice',
            'prayer': 'prayer ask seek'
        }
        
        # Find the best matching topic
        topic_lower = topic.lower()
        best_match = 'hope'  # default
        
        for key, keywords in topic_keywords.items():
            if any(word in topic_lower for word in keywords.split()):
                best_match = key
                break
        
        # Search for verses related to the topic
        search_query = topic_keywords.get(best_match, 'hope future')
        verses = self.bible_api.search_verses(search_query, limit=1)
        
        if verses:
            return verses[0]
        
        # Fallback to a random verse
        return self.bible_api.get_random_verse()

    def generate_daily_post_text(self, verse_data: Dict) -> str:
        """Generate additional text to accompany a daily Bible verse post"""
        try:
            prompt = f"""Given this Bible verse, write a short, informative message (under 280 characters) that could provide additional context for the verse, such as who wrote it, the interpreted meaning of the verse, or a related story that relate to the happenings of the world today:

Verse: "{verse_data['text']}" - {verse_data['reference']}

Write something that:
1. Relates to the verse theme
2. Is encouraging and uplifting  
3. Connects with people's daily lives
4. Is brief enough for Twitter
5. Doesn't just repeat the verse
6. Is informative and not just a repeat of the verse
7. Do not include the actual verse, only the response


Examples:
1.
Verse: "9 If you declare with your mouth, 'Jesus is Lord,' and believe in your heart that God raised him from the dead, you will be saved." - Romans 9:10

Paul, writing in the book of Romans, speaks of arguably the most important declarations of them all. That no matter who you are or what you do, if you believe Jesus is Lord, you are saved.

2. 
Verse:"For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life." - John 3:16

John, one of Jesus's closest disciples, shares this profound message of God's sacrificial love - giving His only Son so that all who believe may have eternal life.

3.
Verse“ 11 ‘For I know the plans I have for you,’ declares the Lord, ‘plans to prosper you and not to harm you, plans to give you hope and a future’” - Jeremiah 29:11

Despite the fact that we have evil in the world, God’s ultimate plan for us is good. We might not always understand in the moment, but the Lord has a way of working everything for his greater purpose.

4.
“ 7 Some trust in chariots and some in horses,  but we trust in the name of the Lord our God.” Psalms 20:7

David, a major writer of the book of Psalms, explains that you should not put your trust in earthly things but in the Lord our God.

"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200  # Increased significantly for detailed, informative responses
            )
            
            generated_text = response.choices[0].message.content.strip()
            return generated_text.strip('"\'')
            
        except Exception as e:
            logger.error(f"Failed to generate daily post text: {e}")
            return "May this verse bless your day! 🙏"

    def select_and_respond_to_tweet(self, tweets: List[Dict]) -> Optional[TweetAnalysisResult]:
        """Analyze a list of tweets and select the best one to respond to with a Bible verse
        
        Follows a 4-step process:
        1. Select best tweet to respond to (AI)
        2. Determine user's mood from tweet (AI) 
        3. Get Bible verse for that mood (API call)
        4. Generate encouraging response with verse (AI)
        
        Args:
            tweets: List of tweet dictionaries from search_tweets
            
        Returns:
            TweetAnalysisResult containing selected tweet, mood, verse, and response
        """
        try:
            if not tweets:
                logger.info("No tweets provided for analysis")
                return None
            
            logger.info(f"🔍 Starting 4-step analysis of {len(tweets)} tweets")
            
            # Convert tweet dictionaries to Tweet objects
            tweet_objects = create_tweets_from_search_results(tweets)
            
            # Step 1: Select the best tweet to respond to
            selected_tweet = self._ai_select_best_tweet(tweet_objects)
            if not selected_tweet:
                return None
            
            # Step 2: Determine the user's mood from the selected tweet
            detected_mood = self._ai_determine_mood(selected_tweet)
            if not detected_mood:
                return None
            
            # Step 3: Get a Bible verse for that mood
            bible_verse = self.bible_api.get_verse_by_mood(detected_mood)
            if not bible_verse:
                return None
            
            # Step 4: Generate encouraging response with the verse
            response_text = self._ai_generate_response(selected_tweet, detected_mood, bible_verse)
            if not response_text:
                return None
            
            return TweetAnalysisResult(
                selected_tweet=selected_tweet,
                detected_mood=detected_mood,
                bible_verse=bible_verse,
                response_text=response_text,
                reasoning=f"Selected for {detected_mood} mood based on content analysis"
            )
            
        except Exception as e:
            logger.error(f"Failed to select and respond to tweet: {e}")
            # Fallback to keyword filtering if AI fails
            logger.info("Falling back to keyword-based filtering")
            return self._fallback_keyword_selection(tweets)

    def _filter_response_candidates(self, tweets: List[Dict]) -> List[Dict]:
        """Filter tweets to find good candidates for spiritual responses"""
        candidates = []
        
        # Keywords that indicate spiritual need or openness
        spiritual_keywords = [
            # Prayer related
            'pray', 'prayer', 'prayers', 'praying', 'pray for me', 'need prayer',
            # Emotional/spiritual struggles
            'struggling', 'difficult time', 'hard time', 'depressed', 'anxious', 
            'worried', 'scared', 'hurt', 'pain', 'lost', 'confused', 'broken',
            'hopeless', 'alone', 'lonely', 'stressed', 'overwhelmed',
            # Spiritual openness
            'god', 'lord', 'jesus', 'faith', 'bible', 'church', 'christian',
            'blessed', 'blessing', 'miracle', 'grace', 'forgiveness',
            # Life events that may need spiritual support
            'funeral', 'passed away', 'died', 'illness', 'sick', 'surgery',
            'job loss', 'unemployed', 'divorce', 'breakup', 'family problems',
            # Expressions of gratitude/praise (good for encouragement)
            'grateful', 'thankful', 'praise', 'amazing grace', 'testimony'
        ]
        
        # Keywords to avoid (controversial, inappropriate, spam-like)
        avoid_keywords = [
            'politics', 'political', 'democrat', 'republican', 'vote', 'election',
            'crypto', 'bitcoin', 'nft', 'trading', 'investment', 'promotion',
            'follow me', 'check out', 'link in bio', 'spam', 'scam',
            'hate', 'angry', 'stupid', 'idiot', 'dumb'
        ]
        
        for tweet in tweets:
            text_lower = tweet['text'].lower()
            
            # Skip retweets (they start with "RT @")
            if tweet['text'].startswith('RT @'):
                continue
            
            # Skip if contains avoid keywords
            if any(avoid_word in text_lower for avoid_word in avoid_keywords):
                continue
            
            # Check for spiritual keywords or emotional need
            has_spiritual_content = any(keyword in text_lower for keyword in spiritual_keywords)
            
            # Also consider tweets with question marks (seeking guidance)
            has_question = '?' in tweet['text']
            
            # Look for emotional indicators even without specific keywords
            emotional_indicators = ['feeling', 'feel', 'need', 'help', 'why', 'how']
            has_emotional_need = any(indicator in text_lower for indicator in emotional_indicators)
            
            if has_spiritual_content or has_question or has_emotional_need:
                # Add candidate with basic analysis
                tweet['candidate_score'] = self._score_tweet_candidacy(tweet)
                candidates.append(tweet)
        
        # Sort by candidate score (highest first)
        candidates.sort(key=lambda x: x.get('candidate_score', 0), reverse=True)
        
        logger.info(f"Found {len(candidates)} candidates after filtering")
        return candidates[:5]  # Limit to top 5 candidates for AI analysis

    def _score_tweet_candidacy(self, tweet: Dict) -> int:
        """Score a tweet's suitability for spiritual response (higher = better)"""
        score = 0
        text_lower = tweet['text'].lower()
        
        # High-priority keywords (clear spiritual/emotional need)
        high_priority = ['pray for me', 'need prayer', 'prayer request', 'struggling', 
                        'depressed', 'anxious', 'lost', 'broken', 'hopeless']
        score += sum(5 for keyword in high_priority if keyword in text_lower)
        
        # Medium-priority keywords
        medium_priority = ['pray', 'prayer', 'god', 'help', 'difficult', 'hurt']
        score += sum(3 for keyword in medium_priority if keyword in text_lower)
        
        # Low-priority indicators
        low_priority = ['feeling', 'why', 'how', 'confused', 'scared']
        score += sum(1 for keyword in low_priority if keyword in text_lower)
        
        # Bonus for questions (seeking guidance)
        if '?' in tweet['text']:
            score += 2
        
        # Bonus for recent tweets (more likely to be seen)
        # Note: created_at comparison would need datetime parsing
        
        return score

    def _ai_select_best_tweet(self, tweets: List[Tweet]) -> Optional[Tweet]:
        """Step 1: Use AI to select the best tweet to respond to"""
        try:
            prompt = """You are InChrist AI, a compassionate Christian bot. Analyze these tweets and select the ONE that would most benefit from a loving, spiritual response.

TWEETS TO ANALYZE:
"""
            
            for i, tweet in enumerate(tweets, 1):
                # Include thread context if available
                context_info = tweet.get_thread_summary()
                
                prompt += f"{i}. ID: {tweet.id}\n"
                prompt += f"   Text: \"{tweet.text}\"\n"
                prompt += f"   Author: {tweet.author_id}"
                if context_info:
                    prompt += f"\n   {context_info}"
                prompt += "\n\n"
            
            prompt += """
FILTERING CRITERIA:
AVOID:
- Political content, drama, arguments
- Commercial/promotional content, spam
- Hateful, aggressive language
- Retweets (starting with "RT @")
- Trolling, sarcasm, inauthentic content
- Controversial wars, such as Israel, Palestine, Iran, Ukraine, etc.
- Controversial figures, e.g. politicans, celebrities, etc.

PRIORITIZE:
- Genuine prayer requests or spiritual seeking
- Emotional struggles (depression, anxiety, grief)
- Life difficulties (illness, loss, problems)
- Questions about faith or meaning
- Authentic vulnerability or calls for help

RESPOND IN JSON:
{
  "selected_tweet_id": "chosen_tweet_id",
  "reasoning": "Why this tweet was selected"
}

If no tweets are suitable:
{
  "selected_tweet_id": null,
  "reasoning": "Why no tweets were suitable"
}
"""

            logger.info("🔍 Step 1: AI selecting best tweet")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temperature for consistent selection
                max_tokens=200
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            import json
            try:
                result = json.loads(ai_response)
            except json.JSONDecodeError:
                logger.warning("AI response not in JSON format")
                return None
            
            if result.get('selected_tweet_id'):
                # Find the selected tweet
                selected_tweet = next((t for t in tweets if t.id == result['selected_tweet_id']), None)
                
                if selected_tweet:
                    logger.info(f"✅ Step 1: Selected tweet {result['selected_tweet_id']}")
                    return selected_tweet
            
            logger.info(f"❌ Step 1: No suitable tweet found - {result.get('reasoning', 'No reason given')}")
            return None
            
        except Exception as e:
            logger.error(f"Step 1 failed: {e}")
            return None

    def _ai_determine_mood(self, selected_tweet: Tweet) -> Optional[str]:
        """Step 2: Use AI to determine the user's mood from the tweet"""
        try:
            # Get available moods from bible_api.py to keep them synced
            available_moods = self.bible_api.get_available_moods()
            
            prompt = f"""Analyze this tweet and determine the person's emotional mood/state.

TWEET: "{selected_tweet.text}"

AVAILABLE MOODS:
{', '.join(available_moods)}

Consider:
- The overall tone and language used
- Explicit emotional expressions
- Implicit feelings behind their words
- Context if this is a reply to another tweet

Choose the ONE mood that best matches their emotional state.

RESPOND IN JSON:
{{
  "detected_mood": "mood_from_list_above",
  "confidence": "high/medium/low",
  "explanation": "Brief explanation of why you chose this mood"
}}

If you cannot determine a clear mood, use "sad" as default.
"""

            logger.info("🔍 Step 2: AI determining mood")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Very low temperature for consistent mood detection
                max_tokens=150
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            import json
            try:
                result = json.loads(ai_response)
                detected_mood = result.get('detected_mood', 'sad')
                
                # Validate the mood is in our available list
                if detected_mood not in available_moods:
                    logger.warning(f"AI returned unknown mood '{detected_mood}', defaulting to 'sad'")
                    detected_mood = 'sad'
                
                logger.info(f"✅ Step 2: Detected mood '{detected_mood}' - {result.get('explanation', '')}")
                return detected_mood
                
            except json.JSONDecodeError:
                logger.warning("AI mood response not in JSON format, defaulting to 'sad'")
                return 'sad'
            
        except Exception as e:
            logger.error(f"Step 2 failed: {e}, defaulting to 'sad'")
            return 'sad'

    def _ai_generate_response(self, selected_tweet: Tweet, mood: str, bible_verse: Dict) -> Optional[str]:
        """Step 4: Use AI to generate encouraging response with Bible verse"""
        try:
            prompt = f"""Generate a compassionate response to this person who is feeling {mood}.

THEIR TWEET: "{selected_tweet.text}"
DETECTED MOOD: {mood}

BIBLE VERSE TO INCLUDE:
"{bible_verse['text']}" - {bible_verse['reference']} ({bible_verse['version']})

RESPONSE REQUIREMENTS:
- Under 280 characters for Twitter
- Warm, encouraging, and supportive tone
- Include the complete Bible verse and reference
- Address their specific situation/mood
- Sound natural and human, not robotic
- Don't be preachy or judgmental
- Match the tone to their need (comfort, hope, peace, etc.)

RESPONSE FORMAT:
Generate ONLY the tweet response text, nothing else. Do not include quotes around it.

EXAMPLES:
- For sadness: "I'm sorry you're going through this. Remember: 'The Lord is close to the brokenhearted...' - Psalm 34:18. You're not alone 💙"
- For anxiety: "Feeling anxious? 'Do not be anxious about anything, but in every situation...' - Philippians 4:6. God's peace is with you 🙏"
- For fear: "When fear overwhelms: 'When I am afraid, I put my trust in you' - Psalm 56:3. You are stronger than you know ✨"
"""

            logger.info("🔍 Step 4: AI generating response")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,  # Moderate temperature for creative but focused responses
                max_tokens=120  # Enough for a tweet-length response
            )
            
            generated_response = response.choices[0].message.content.strip()
            
            # Clean up any quotes the AI might have added
            generated_response = generated_response.strip('"\'')
            
            # Ensure it fits Twitter's character limit
            if len(generated_response) > 280:
                logger.warning(f"Response too long ({len(generated_response)} chars), truncating")
                generated_response = generated_response[:277] + "..."
            
            logger.info(f"✅ Step 4: Generated response ({len(generated_response)} chars)")
            return generated_response
            
        except Exception as e:
            logger.error(f"Step 4 failed: {e}")
            # Fallback response
            return f"🙏 \"{bible_verse['text']}\" - {bible_verse['reference']} ({bible_verse['version']})"

    def _ai_filter_select_and_respond(self, tweets: List[Dict]) -> Optional[Dict]:
        """Use AI to filter, select, and respond to the best tweet from the full list"""
        try:
            # Build prompt with all tweets
            prompt = """You are InChrist AI, a compassionate Christian bot that responds to people in need with Bible verses and encouragement.

TASK: Analyze ALL these tweets and select the ONE that would most benefit from a loving, spiritual response with a relevant Bible verse.

TWEETS TO ANALYZE:
"""
            
            for i, tweet in enumerate(tweets, 1):
                # Include thread context if available
                context_info = ""
                if tweet.get('is_reply') and tweet.get('thread_context'):
                    original = tweet['thread_context'].get('original_tweet')
                    if original:
                        context_info = f"\n   (This is a reply to: \"{original['text'][:100]}...\")"
                
                prompt += f"{i}. Tweet ID: {tweet['id']}\n"
                prompt += f"   Text: \"{tweet['text']}\"\n"
                prompt += f"   Author: {tweet['author_id']}{context_info}\n\n"
            
            prompt += """
FILTERING & SELECTION CRITERIA:
AVOID these types of tweets:
- Political content (elections, politicians, political parties, controversial political topics)
- Drama, arguments, or negative interactions between users
- Commercial/promotional content (crypto, NFTs, investment schemes, "follow me", spam)
- Hateful, angry, or aggressive language
- Retweets that just repeat others' content (starting with "RT @")
- Obvious trolling, sarcasm, or inauthentic content

PRIORITIZE these types of tweets:
- Genuine prayer requests ("pray for me", "need prayer", "prayer request")
- People expressing emotional struggles (depression, anxiety, grief, loneliness)
- Spiritual seeking or questions about faith, God, life meaning
- People going through difficult life events (illness, loss, family problems)
- Expressions of gratitude that could use encouragement
- Authentic emotional vulnerability or calls for help

RESPONSE REQUIREMENTS:
- Generate a compassionate, helpful response under 280 characters
- Include a relevant Bible verse that specifically addresses their situation/mood
- Be encouraging and supportive, never preachy, judgmental, or pushy
- Match the tone to their need (comfort for grief, hope for despair, peace for anxiety, etc.)
- Sound natural and human, not robotic

OUTPUT FORMAT:
{
  "selected_tweet_id": "the_chosen_tweet_id",
  "reasoning": "Brief explanation of why this tweet was selected and why others were filtered out",
  "response": "Your complete response with Bible verse"
}

If NO tweets are suitable for a spiritual response, return:
{
  "selected_tweet_id": null,
  "reasoning": "No suitable candidates found - explain what types of content were found and why they weren't appropriate",
  "response": null
}
"""

            logger.info("Sending all tweets to AI for intelligent filtering, selection, and response generation")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more focused analysis
                max_tokens=400  # Increased for more detailed reasoning
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse the AI response (it should be JSON-like)
            import json
            try:
                result = json.loads(ai_response)
            except json.JSONDecodeError:
                # Fallback parsing if AI doesn't return perfect JSON
                logger.warning("AI response not in JSON format, attempting manual parsing")
                result = self._parse_ai_response_fallback(ai_response, tweets)
            
            if result.get('selected_tweet_id'):
                # Find the selected tweet
                selected_tweet = next((t for t in tweets if t['id'] == result['selected_tweet_id']), None)
                
                if selected_tweet:
                    logger.info(f"AI selected tweet {result['selected_tweet_id']}: {result['reasoning']}")
                    return {
                        'selected_tweet': selected_tweet,
                        'response_text': result['response'],
                        'reasoning': result['reasoning']
                    }
            
            logger.info(f"AI determined no suitable tweets for response: {result.get('reasoning', 'No reason given')}")
            return None
            
        except Exception as e:
            logger.error(f"Failed in AI filtering and selection: {e}")
            return None

    def _parse_ai_response_fallback(self, ai_text: str, candidates: List[Dict]) -> Dict:
        """Fallback parsing when AI doesn't return proper JSON"""
        result = {"selected_tweet_id": None, "reasoning": "Parsing failed", "response": None}
        
        # Look for tweet ID in the response
        for candidate in candidates:
            if candidate['id'] in ai_text:
                result['selected_tweet_id'] = candidate['id']
                break
        
        # Extract response if possible (look for quotes)
        import re
        response_match = re.search(r'"([^"]*(?:Bible|verse|God|Jesus|Lord)[^"]*)"', ai_text)
        if response_match:
            result['response'] = response_match.group(1)
        
        return result

    def _fallback_keyword_selection(self, tweets: List[Dict]) -> Optional[Dict]:
        """Fallback to keyword-based filtering when AI fails"""
        try:
            # Use the old keyword filtering as backup
            candidates = self._filter_response_candidates(tweets)
            
            if candidates:
                # Select the highest-scored candidate
                best_candidate = candidates[0]
                return self._fallback_selection_and_response(best_candidate)
            
            return None
            
        except Exception as e:
            logger.error(f"Fallback keyword selection failed: {e}")
            return None

    def _fallback_selection_and_response(self, tweet: Dict) -> Dict:
        """Generate a fallback response when AI analysis fails"""
        # Analyze the tweet intent using existing logic
        intent = self._analyze_intent(tweet['text'])
        
        # Get appropriate Bible verse
        verse_data = self.get_verse_for_topic(intent)
        
        # Create simple response
        if verse_data:
            response = f"🙏 \"{verse_data['text']}\" - {verse_data['reference']}"
        else:
            response = self._get_fallback_response(tweet['text'])
        
        return {
            'selected_tweet': tweet,
            'response_text': response,
            'reasoning': f"Fallback selection - detected {intent} intent"
        }
