# Cloud deployment configuration using environment variables
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Twitter API Credentials - use environment variables for security
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")

# OpenAI API Key for AI responses
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Bible API Configuration
BIBLE_API_KEY = os.getenv("BIBLE_API_KEY", "23bd2bde169995d3ba3e52177332d811")  # Default fallback
BIBLE_API_URL = "https://api.scripture.api.bible/v1"

# Bot Configuration
BOT_USERNAME = os.getenv("BOT_USERNAME", "InChristAI")
TWITTER_USER_ID = os.getenv("TWITTER_USER_ID", "1967203305995595776")
POSTING_TIME = os.getenv("POSTING_TIME", "08:00")  # 24-hour format
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")

# Database - support both SQLite (local) and PostgreSQL (cloud)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///inchrist_ai.db")

# AI Response Configuration
MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "180"))
AI_MODEL = os.getenv("AI_MODEL", "gpt-3.5-turbo")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))

# Cloud deployment settings
PORT = int(os.getenv("PORT", 8080))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
