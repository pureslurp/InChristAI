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
        ]

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
