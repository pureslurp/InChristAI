"""
Bible API integration for fetching daily verses
"""
import requests
import random
import logging
from typing import Dict, Optional, List
# Use cloud config if available, fallback to local config
try:
    import config_cloud as config
except ImportError:
    import config

logger = logging.getLogger(__name__)

class BibleAPI:
    def __init__(self):
        self.api_key = config.BIBLE_API_KEY
        self.base_url = config.BIBLE_API_URL
        self.headers = {
            'api-key': self.api_key,
            'Accept': 'application/json'
        }
        
        # Popular Bible versions
        self.bible_versions = {
            'ESV': 'de4e12af7f28f599-02',  # English Standard Version
            'NIV': '71c6eab17ae5b667-01',  # New International Version
            'KJV': 'de4e12af7f28f599-01',  # King James Version
            'NLT': '71c6eab17ae5b667-04',  # New Living Translation
        }
        
        # Inspirational books and chapters for daily verses
        self.popular_passages = [
            'PSA.23',    # Psalm 23
            'PSA.91',    # Psalm 91
            'PSA.119',   # Psalm 119
            'PRO.3',     # Proverbs 3
            'PRO.31',    # Proverbs 31
            'ISA.40',    # Isaiah 40
            'ISA.41',    # Isaiah 41
            'JER.29',    # Jeremiah 29
            'MAT.5',     # Matthew 5 (Beatitudes)
            'MAT.6',     # Matthew 6 (Lord's Prayer)
            'JHN.3',     # John 3
            'JHN.14',    # John 14
            'ROM.8',     # Romans 8
            'ROM.12',    # Romans 12
            '1CO.13',    # 1 Corinthians 13 (Love Chapter)
            'GAL.5',     # Galatians 5
            'EPH.6',     # Ephesians 6
            'PHP.4',     # Philippians 4
            'COL.3',     # Colossians 3
            '1TH.5',     # 1 Thessalonians 5
            '2TI.3',     # 2 Timothy 3
            'HEB.11',    # Hebrews 11 (Faith Chapter)
            'JAS.1',     # James 1
            '1PE.5',     # 1 Peter 5
            '1JN.4',     # 1 John 4
            'MAT.4',     # Matthew 4
            'MAT.5',     # Matthew 5 -- Sermon on the Mount
            'MAT.6',     # Matthew 6 -- Lord's Prayer
            'MAT.7',     # Matthew 7 -- Sermon on the Mount
            'MAT.17',    # Matthew 17 -- Transfiguration
            'MAT.18',    # Matthew 18 -- Discipleship
            'MAT.19',    # Matthew 19 -- The Law and the Prophets
            'MRK.4', # Mark 4 -- Parables
            'MRK.10',   # Mark 10 -- Parables
            '1CO.1', # 1 Corinthians 1 -- Paul's Prayer
            '1CO.2', # 1 Corinthians 2 -- Paul's Wisdom
            '1CO.3', # 1 Corinthians 3 -- Paul's Building
            'GAL.5', # Galatians 5 -- Paul's Freedom
            'EPH.5', # Ephesians 5 -- Paul's Love
            'EPH.6', # Ephesians 6 -- Paul's Authority
            'COL.3', # Colossians 3 -- Paul's Mind
            '1PE.2', # 1 Peter 2 -- Paul's New Birth 
        ]
        
        # Bible verses for different moods and emotions
        # Format: BOOK.CHAPTER.VERSE compatible with API.Bible
        
        self.afraid = [
            'PSA.34.4',    # "I sought the Lord, and he answered me; he delivered me from all my fears."
            'MAT.10.28',   # "Do not be afraid of those who kill the body but cannot kill the soul."
            'PSA.56.3',    # "When I am afraid, I put my trust in you."
            'ISA.41.10',   # "So do not fear, for I am with you; do not be dismayed..."
            'JOS.1.9',     # "Have I not commanded you? Be strong and courageous."
            'PSA.27.1',    # "The Lord is my light and my salvation—whom shall I fear?"
            'HEB.13.6',    # "So we say with confidence, 'The Lord is my helper; I will not be afraid.'"
            'PSA.118.6',   # "The Lord is with me; I will not be afraid."
            'ISA.43.1',    # "Do not fear, for I have redeemed you; I have summoned you by name; you are mine."
            'DEU.31.6'     # "Be strong and courageous. Do not be afraid or terrified..."
        ]
        
        self.anxious = [
            'PHP.4.6',     # "Do not be anxious about anything, but in every situation..."
            'PHP.4.7',     # "And the peace of God, which transcends all understanding..."
            'MAT.6.26',    # "Look at the birds of the air; they do not sow or reap..."
            'MAT.6.34',    # "Therefore do not worry about tomorrow, for tomorrow will worry about itself."
            '1PE.5.7',     # "Cast all your anxiety on him because he cares for you."
            'PSA.55.22',   # "Cast your cares on the Lord and he will sustain you..."
            'ISA.26.3',    # "You will keep in perfect peace those whose minds are steadfast..."
            'JHN.14.27',   # "Peace I leave with you; my peace I give you."
            'PSA.94.19',   # "When anxiety was great within me, your consolation brought me joy."
            'LUK.12.25'    # "Who of you by worrying can add a single hour to your life?"
        ]
        
        self.lonely = [
            'DEU.31.6',    # "Be strong and courageous. Do not be afraid... the Lord your God goes with you"
            'HEB.13.5',    # "Never will I leave you; never will I forsake you."
            'PSA.139.7',   # "Where can I go from your Spirit? Where can I flee from your presence?"
            'ISA.41.10',   # "So do not fear, for I am with you; do not be dismayed..."
            'MAT.28.20',   # "And surely I am with you always, to the very end of the age."
            'PSA.68.6',    # "God sets the lonely in families, he leads out the prisoners with singing"
            'JHN.14.18',   # "I will not leave you as orphans; I will come to you."
            'PSA.25.16',   # "Turn to me and be gracious to me, for I am lonely and afflicted."
            '1KI.19.10',   # Story of Elijah when he felt alone
            'PSA.27.10'    # "Though my father and mother forsake me, the Lord will receive me."
        ]
        
        self.sad = [
            'PSA.34.18',   # "The Lord is close to the brokenhearted and saves those who are crushed in spirit."
            'PSA.147.3',   # "He heals the brokenhearted and binds up their wounds."
            'MAT.5.4',     # "Blessed are those who mourn, for they will be comforted."
            'JHN.16.33',   # "In this world you will have trouble. But take heart! I have overcome the world."
            'REV.21.4',    # "He will wipe every tear from their eyes. There will be no more death..."
            'PSA.30.5',    # "Weeping may stay for the night, but rejoicing comes in the morning."
            '2CO.1.4',     # "Who comforts us in all our troubles, so that we can comfort those..."
            'ISA.61.3',    # "To bestow on them a crown of beauty instead of ashes..."
            'PSA.42.11',   # "Why, my soul, are you downcast? Put your hope in God..."
            'LAM.3.22'     # "Because of the Lord's great love we are not consumed..."
        ]
        
        self.angry = [
            'EPH.4.26',    # "In your anger do not sin: Do not let the sun go down while you are still angry."
            'PRO.29.11',   # "Fools give full vent to their rage, but the wise bring calm in the end."
            'JAS.1.19',    # "Everyone should be quick to listen, slow to speak and slow to become angry."
            'JAS.1.20',    # "Because human anger does not produce the righteousness that God desires."
            'PRO.15.1',    # "A gentle answer turns away wrath, but a harsh word stirs up anger."
            'PRO.16.32',   # "Better a patient person than a warrior, one with self-control than one who takes a city."
            'COL.3.8',     # "But now you must also rid yourselves of all such things as these: anger, rage..."
            'EPH.4.31',    # "Get rid of all bitterness, rage and anger, brawling and slander..."
            'PSA.37.8',    # "Refrain from anger and turn from wrath; do not fret—it leads only to evil."
            'GAL.5.22'     # "But the fruit of the Spirit is love, joy, peace, forbearance, kindness..."
        ]
        
        self.confused = [
            'PRO.3.5',     # "Trust in the Lord with all your heart and lean not on your own understanding"
            'PRO.3.6',     # "In all your ways submit to him, and he will make your paths straight."
            'JAS.1.5',     # "If any of you lacks wisdom, you should ask God, who gives generously..."
            '1CO.14.33',   # "For God is not a God of disorder but of peace..."
            'PSA.32.8',    # "I will instruct you and teach you in the way you should go..."
            'ISA.30.21',   # "Whether you turn to the right or to the left, your ears will hear a voice behind you"
            'JER.33.3',    # "Call to me and I will answer you and tell you great and unsearchable things"
            'PSA.119.105', # "Your word is a lamp for my feet, a light on my path."
            'JHN.16.13',   # "But when he, the Spirit of truth, comes, he will guide you into all the truth."
            'PRO.27.9'     # "Perfume and incense bring joy to the heart, and the pleasantness of a friend springs from their heartfelt advice."
        ]
        
        self.discouraged = [
            'ISA.40.31',   # "But those who hope in the Lord will renew their strength..."
            'PSA.42.5',    # "Why, my soul, are you downcast? Put your hope in God..."
            'JHN.16.33',   # "In this world you will have trouble. But take heart! I have overcome the world."
            'PHP.4.13',    # "I can do all this through him who gives me strength."
            'GAL.6.9',     # "Let us not become weary in doing good, for at the proper time we will reap"
            'PSA.73.26',   # "My flesh and my heart may fail, but God is the strength of my heart"
            '2CO.4.16',    # "Therefore we do not lose heart. Though outwardly we are wasting away..."
            'PSA.31.24',   # "Be strong and take heart, all you who hope in the Lord."
            'HEB.12.3',    # "Consider him who endured such opposition from sinners, so that you will not grow weary"
            'ROM.8.28'     # "And we know that in all things God works for the good of those who love him"
        ]
        
        self.guilty = [
            '1JN.1.9',     # "If we confess our sins, he is faithful and just and will forgive us"
            'PSA.51.1',    # "Have mercy on me, O God, according to your unfailing love"
            'PSA.51.10',   # "Create in me a pure heart, O God, and renew a steadfast spirit within me."
            'ROM.8.1',     # "Therefore, there is now no condemnation for those who are in Christ Jesus"
            'ISA.43.25',   # "I, even I, am he who blots out your transgressions, for my own sake"
            'PSA.103.12',  # "As far as the east is from the west, so far has he removed our transgressions"
            'MIC.7.18',    # "Who is a God like you, who pardons sin and forgives the transgression"
            'ACT.3.19',    # "Repent, then, and turn to God, so that your sins may be wiped out"
            'PSA.32.5',    # "Then I acknowledged my sin to you and did not cover up my iniquity"
            'EPH.1.7'      # "In him we have redemption through his blood, the forgiveness of sins"
        ]
        
        self.stressed = [
            'MAT.11.28',   # "Come to me, all you who are weary and burdened, and I will give you rest."
            'PSA.23.1',    # "The Lord is my shepherd, I lack nothing."
            'PSA.23.2',    # "He makes me lie down in green pastures, he leads me beside quiet waters"
            'ISA.26.3',    # "You will keep in perfect peace those whose minds are steadfast"
            'JHN.14.27',   # "Peace I leave with you; my peace I give you."
            'PHP.4.19',    # "And my God will meet all your needs according to the riches of his glory"
            'PSA.55.22',   # "Cast your cares on the Lord and he will sustain you"
            'MAT.6.26',    # "Look at the birds of the air; they do not sow or reap"
            'PSA.46.10',   # "Be still, and know that I am God"
            '2TH.3.16'     # "Now may the Lord of peace himself give you peace at all times"
        ]
        
        self.hopeless = [
            'JER.29.11',   # "For I know the plans I have for you," declares the Lord, "plans to prosper you"
            'ROM.15.13',   # "May the God of hope fill you with all joy and peace as you trust in him"
            'PSA.42.5',    # "Why, my soul, are you downcast? Put your hope in God"
            'LAM.3.21',    # "Yet this I call to mind and therefore I have hope"
            'LAM.3.22',    # "Because of the Lord's great love we are not consumed"
            'HEB.6.19',    # "We have this hope as an anchor for the soul, firm and secure"
            'ISA.40.31',   # "But those who hope in the Lord will renew their strength"
            'PSA.71.14',   # "As for me, I will always have hope; I will praise you more and more"
            'ROM.5.5',     # "And hope does not put us to shame, because God's love has been poured out"
            'JOB.11.18'    # "You will be secure, because there is hope; you will look about you and take your rest in safety"
        ]
        
        self.grateful = [
            'PSA.100.4',   # "Enter his gates with thanksgiving and his courts with praise"
            '1TH.5.18',    # "Give thanks in all circumstances; for this is God's will for you in Christ Jesus"
            'PHP.4.6',     # "Do not be anxious about anything, but in every situation, by prayer and petition, with thanksgiving"
            'COL.3.17',    # "And whatever you do, whether in word or deed, do it all in the name of the Lord Jesus, giving thanks"
            'PSA.107.1',   # "Give thanks to the Lord, for he is good; his love endures forever"
            'EPH.5.20',    # "Always giving thanks to God the Father for everything, in the name of our Lord Jesus Christ"
            'PSA.118.24',  # "The Lord has done it this very day; let us rejoice today and be glad"
            'PSA.103.2',   # "Praise the Lord, my soul, and forget not all his benefits"
            'HEB.13.15',   # "Through Jesus, therefore, let us continually offer to God a sacrifice of praise"
            'PSA.136.1'    # "Give thanks to the Lord, for he is good. His love endures forever"
        ]
        
        self.jealous = [
            'PRO.14.30',   # "A heart at peace gives life to the body, but envy rots the bones"
            'GAL.5.26',    # "Let us not become conceited, provoking and envying each other"
            'JAS.3.16',    # "For where you have envy and selfish ambition, there you find disorder"
            '1CO.13.4',    # "Love is patient, love is kind. It does not envy, it does not boast"
            'ROM.13.13',   # "Let us behave decently, as in the daytime, not in carousing and drunkenness, not in sexual immorality and debauchery, not in dissension and jealousy"
            'TIT.3.3',     # "At one time we too were foolish, disobedient, deceived and enslaved by all kinds of passions and pleasures. We lived in malice and envy"
            'GAL.5.19',    # "The acts of the flesh are obvious: sexual immorality, impurity and debauchery; idolatry and witchcraft; hatred, discord, jealousy"
            'PRO.27.4',    # "Anger is cruel and fury overwhelming, but who can stand before jealousy?"
            'ECC.4.4',     # "And I saw that all toil and all achievement spring from one person's envy of another"
            '1PE.2.1'      # "Therefore, rid yourselves of all malice and all deceit, hypocrisy, envy, and slander of every kind"
        ]

    def get_available_moods(self) -> List[str]:
        """Get list of all available mood categories"""
        return [
            'afraid', 'anxious', 'lonely', 'sad', 'angry', 'confused',
            'discouraged', 'guilty', 'stressed', 'hopeless', 'grateful', 'jealous'
        ]

    def get_verse_by_mood(self, mood: str, version: str = 'ESV') -> Optional[Dict]:
        """Get a random verse reference for a specific mood"""
        # Use getattr to dynamically access the mood attribute, default to 'sad' if mood doesn't exist
        mood_verses = getattr(self, mood, self.sad)
        verse_reference = random.choice(mood_verses)
        
        # Get the full verse data using the reference
        return self.get_verse_by_reference(verse_reference, version)
    def get_random_verse(self, version: str = 'ESV') -> Optional[Dict]:
        """Get a random inspirational verse"""
        try:
            # Select random chapter from popular passages
            chapter = random.choice(self.popular_passages)
            bible_id = self.bible_versions.get(version, self.bible_versions['ESV'])
            
            # Get chapter content
            url = f"{self.base_url}/bibles/{bible_id}/chapters/{chapter}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                chapter_data = response.json()
                
                # Get verses from the chapter
                verses_url = f"{self.base_url}/bibles/{bible_id}/chapters/{chapter}/verses"
                verses_response = requests.get(verses_url, headers=self.headers)
                
                if verses_response.status_code == 200:
                    verses_data = verses_response.json()
                    verses = verses_data.get('data', [])
                    
                    if verses:
                        # Select a random verse
                        random_verse = random.choice(verses)
                        verse_id = random_verse['id']
                        
                        # Get the full verse content
                        verse_url = f"{self.base_url}/bibles/{bible_id}/verses/{verse_id}"
                        verse_response = requests.get(verse_url, headers=self.headers)
                        
                        if verse_response.status_code == 200:
                            verse_data = verse_response.json()
                            verse_content = verse_data['data']
                            
                            return {
                                'reference': verse_content['reference'],
                                'text': self._clean_verse_text(verse_content['content']),
                                'version': version
                            }
            
            logger.error(f"Failed to fetch verse: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching random verse: {e}")
            return None

    def get_verse_by_reference(self, reference: str, version: str = 'ESV') -> Optional[Dict]:
        """Get a specific verse by reference (e.g., 'JHN.3.16')"""
        try:
            bible_id = self.bible_versions.get(version, self.bible_versions['ESV'])
            url = f"{self.base_url}/bibles/{bible_id}/verses/{reference}"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                verse_data = response.json()
                verse_content = verse_data['data']
                
                return {
                    'reference': verse_content['reference'],
                    'text': self._clean_verse_text(verse_content['content']),
                    'version': version
                }
            
            logger.error(f"Failed to fetch verse {reference}: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching verse {reference}: {e}")
            return None

    def search_verses(self, query: str, version: str = 'ESV', limit: int = 5) -> List[Dict]:
        """Search for verses containing specific keywords"""
        try:
            bible_id = self.bible_versions.get(version, self.bible_versions['ESV'])
            url = f"{self.base_url}/bibles/{bible_id}/search"
            
            params = {
                'query': query,
                'limit': limit
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                search_data = response.json()
                verses = search_data.get('data', {}).get('verses', [])
                
                result = []
                for verse in verses:
                    result.append({
                        'reference': verse['reference'],
                        'text': self._clean_verse_text(verse['text']),
                        'version': version
                    })
                
                return result
            
            logger.error(f"Failed to search verses: {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"Error searching verses: {e}")
            return []

    def _clean_verse_text(self, text: str) -> str:
        """Clean HTML tags and formatting from verse text"""
        import re
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())
        return clean_text

    def get_daily_verse(self) -> Optional[Dict]:
        """Get a verse for daily posting - could be random or follow a reading plan"""
        return self.get_random_verse()

# Fallback verses for when API is unavailable
FALLBACK_VERSES = [
    {
        'reference': 'John 3:16',
        'text': 'For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.',
        'version': 'NIV'
    },
    {
        'reference': 'Philippians 4:13',
        'text': 'I can do all this through him who gives me strength.',
        'version': 'NIV'
    },
    {
        'reference': 'Jeremiah 29:11',
        'text': 'For I know the plans I have for you," declares the Lord, "plans to prosper you and not to harm you, to give you hope and a future.',
        'version': 'NIV'
    },
    {
        'reference': 'Romans 8:28',
        'text': 'And we know that in all things God works for the good of those who love him, who have been called according to his purpose.',
        'version': 'NIV'
    },
    {
        'reference': 'Psalm 23:1',
        'text': 'The Lord is my shepherd, I lack nothing.',
        'version': 'NIV'
    }
]

def get_fallback_verse() -> Dict:
    """Return a random fallback verse when API is unavailable"""
    return random.choice(FALLBACK_VERSES)
