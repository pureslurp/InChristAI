# InChrist AI - Twitter Bot

A Christian AI agent for Twitter/X that posts daily Bible verses and interacts with users in an encouraging, faith-based way.

## Features

- 📖 **Daily Bible Verse Posting**: Automatically posts inspiring Bible verses daily
- 🤖 **AI-Powered Responses**: Responds to mentions with contextual, encouraging messages
- 💬 **Smart Interactions**: Analyzes mention intent (prayer requests, comfort needed, questions)
- 📊 **Analytics & Tracking**: Monitors interactions and maintains response history
- 🛡️ **Rate Limiting**: Built-in spam protection and rate limiting
- 🎯 **Themed Content**: Support for themed verse weeks (hope, love, strength, etc.)

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Twitter Developer Account with API access
- OpenAI API key
- Bible API key (optional - has fallback verses)

### 2. Installation

```bash
# Clone or download the project
cd InChristAI

# Install dependencies
pip install -r requirements.txt

# Run setup
python setup.py
```

### 3. Configuration

1. **Copy the configuration template:**
   ```bash
   cp config_example.py config.py
   ```

2. **Edit `config.py` with your API credentials:**

#### Twitter API Setup
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app
3. Generate API keys and tokens
4. Add them to `config.py`:
   ```python
   TWITTER_API_KEY = "your_api_key"
   TWITTER_API_SECRET = "your_api_secret"
   TWITTER_ACCESS_TOKEN = "your_access_token"
   TWITTER_ACCESS_TOKEN_SECRET = "your_access_token_secret"
   TWITTER_BEARER_TOKEN = "your_bearer_token"
   ```

#### OpenAI API Setup
1. Get API key from [OpenAI](https://platform.openai.com/)
2. Add to `config.py`:
   ```python
   OPENAI_API_KEY = "your_openai_api_key"
   ```

#### Bible API Setup (Optional)
1. Get free API key from [Scripture API](https://scripture.api.bible/)
2. Add to `config.py`:
   ```python
   BIBLE_API_KEY = "your_bible_api_key"
   ```

#### Bot Configuration
```python
BOT_USERNAME = "your_bot_twitter_username"
POSTING_TIME = "08:00"  # Daily posting time (24-hour format)
TIMEZONE = "America/New_York"
```

### 4. Verify Setup

```bash
# Check configuration
python setup.py check

# Test API connections
python main.py status
```

## Usage

### Starting the Bot

```bash
# Start with full scheduling (recommended for production)
python main.py start

# Or simply:
python main.py
```

### Manual Commands

```bash
# Post today's verse once
python main.py post_verse

# Check and respond to mentions once
python main.py check_mentions

# Show bot statistics
python main.py stats

# Show bot status
python main.py status

# Run database cleanup
python main.py cleanup

# Show help
python main.py help
```

## Bot Behavior

### Daily Posting
- Posts a Bible verse every day at the configured time
- Uses different posting styles for variety
- Includes relevant hashtags and emojis
- Falls back to preset verses if API fails

### Interaction Handling
- Monitors mentions and replies intelligently
- Analyzes intent (prayer requests, questions, encouragement needed)
- Generates contextual AI responses
- Includes relevant Bible verses in responses
- Rate limits to prevent spam

### Response Types
- **Prayer Requests**: Offers prayer and comfort verses
- **Questions**: Provides helpful, biblically-grounded answers
- **Encouragement Needed**: Shares hope and strength verses
- **Gratitude**: Celebrates with thanksgiving verses
- **General**: Friendly, encouraging responses

## File Structure

```
InChristAI/
├── main.py                 # Main application entry point
├── config_example.py       # Configuration template
├── setup.py               # Setup and configuration checker
├── bible_api.py           # Bible verse API integration
├── twitter_api.py         # Twitter API wrapper
├── ai_responses.py        # AI response generation
├── daily_poster.py        # Daily verse posting
├── interaction_handler.py # Mention processing and responses
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── inchrist_ai.db        # SQLite database (created automatically)
```

## Database

The bot uses SQLite to track:
- Daily posts and verse history
- User interactions and responses
- Rate limiting and spam prevention
- Analytics and statistics

## Customization

### Adding New Verse Sources
Edit `bible_api.py` to add more Bible versions or verse collections.

### Modifying Response Styles
Edit `ai_responses.py` to customize the AI personality and response patterns.

### Changing Posting Schedule
Edit the scheduling in `main.py` or modify `POSTING_TIME` in config.

### Themed Content
Use the themed week functionality in `daily_poster.py` for special occasions.

## Monitoring

### Logs
- Application logs are saved to `inchrist_ai.log`
- Use `tail -f inchrist_ai.log` to monitor in real-time

### Statistics
```bash
python main.py stats
```
Shows:
- Total interactions
- Response success rate
- Daily activity
- Unique users reached

## Troubleshooting

### Common Issues

1. **"Failed to verify Twitter credentials"**
   - Check API keys in `config.py`
   - Ensure Twitter app has read/write permissions

2. **"OpenAI API error"**
   - Verify OpenAI API key
   - Check account credits/billing

3. **"Bible API failed"**
   - Bot will use fallback verses
   - Check Bible API key if needed

4. **Rate limiting errors**
   - Twitter has rate limits - bot includes built-in handling
   - Consider reducing interaction frequency

### Getting Help

1. Check logs in `inchrist_ai.log`
2. Run `python main.py status` for diagnostics
3. Verify configuration with `python setup.py check`

## Best Practices

- **Test thoroughly** before running in production
- **Monitor regularly** for any issues or inappropriate responses
- **Backup your database** periodically
- **Review interaction logs** to improve responses
- **Stay within API rate limits** to avoid suspension

## Contributing

This is a template for creating Christian Twitter bots. Feel free to:
- Customize for your specific ministry needs
- Add new features like image posting
- Integrate with other Bible study resources
- Improve the AI response quality

## License

This project is provided as-is for educational and ministry purposes. Please ensure compliance with Twitter's Terms of Service and API usage guidelines.

## Disclaimer

This bot is designed to share encouraging Christian content. Always review and test thoroughly before deploying. The creators are not responsible for any issues arising from bot usage.
