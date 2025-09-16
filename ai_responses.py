"""
AI-powered response generation for Twitter interactions
"""
import openai
import logging
from typing import Dict, List, Optional
import re
import config
from bible_api import BibleAPI

logger = logging.getLogger(__name__)

class AIResponseGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.AI_MODEL
        self.temperature = config.AI_TEMPERATURE
        self.max_response_length = config.MAX_RESPONSE_LENGTH
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
            
            # Generate response using OpenAI
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
        
        if user_info:
            base_prompt += f"\nUser info: @{user_info.get('username', 'unknown')}"
        
        if context:
            base_prompt += f"\nContext: {context}"
        
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
        
        base_prompt += "\n\nGenerate a tweet-length response (under 280 characters) that is warm, genuine, and helpful."
        
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
