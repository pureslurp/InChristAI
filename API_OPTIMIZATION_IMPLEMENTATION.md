# X API Free Tier Optimization - Implementation Summary

## Problem Identified

You discovered that **each tweet returned from a search counts as a separate API call**, not just the search request itself. This means:
- **Before:** 1 search returning 10 tweets = 10 API calls/day = ~300 calls/month ❌
- **Limit:** 100 calls/month on X API Free tier

## Solution Implemented

### Configuration Options Added

Two new configuration options have been added to `config.py` and `config_cloud.py`:

1. **`PRAYER_SEARCH_COUNT`** (default: 5)
   - Number of tweets to return per search
   - Each tweet = 1 API call
   - Recommended: 5 (good diversity, reasonable cost)

2. **`PRAYER_SEARCH_INTERVAL_DAYS`** (default: 3)
   - How often to run the prayer search
   - 1 = daily, 2 = every other day, 3 = every 3 days, etc.
   - Recommended: 3 (every 3 days)

### Default Strategy (Recommended)

**Current Settings:**
- Search count: 5 tweets
- Search frequency: Every 3 days
- Mentions: Daily (unchanged)

**Expected Monthly Usage:**
- Mentions: ~30 calls/month (1/day)
- Prayer Search: ~50 calls/month (5 calls every 3 days)
- **Total: ~80 calls/month**
- **Buffer: 20 calls (20% safety margin)** ✅

### How It Works

1. **Database Tracking**: The bot now uses a `bot_state` table to track when the last search was run, ensuring the interval is respected even after restarts.

2. **Automatic Projection**: On startup, the bot calculates and displays:
   - Expected monthly usage for each feature
   - Total expected usage
   - Remaining buffer
   - Warnings if usage is too high

3. **Flexible Configuration**: You can easily adjust the strategy by changing the config values:
   ```python
   PRAYER_SEARCH_COUNT = 5  # Change to 3 for more conservative, or 7 for more diversity
   PRAYER_SEARCH_INTERVAL_DAYS = 3  # Change to 2 for more frequent, or 4 for more conservative
   ```

## Alternative Strategies

See `API_OPTIMIZATION_STRATEGIES.md` for detailed analysis of other strategies you could use:

- **Strategy 2**: 5 tweets every 2 days = ~105 calls/month (slightly over, but manageable)
- **Strategy 3**: 5 tweets 3x per week = ~90 calls/month (10% buffer)
- **Strategy 4**: 3 tweets every 2 days = ~75 calls/month (25% buffer, less diversity)
- **Strategy 5**: 5 tweets 2x per week = ~70 calls/month (30% buffer, very infrequent)

## Files Modified

1. **`config.py`** - Added `PRAYER_SEARCH_COUNT` and `PRAYER_SEARCH_INTERVAL_DAYS`
2. **`config_cloud.py`** - Added same config options with environment variable support
3. **`main.py`** - Updated to:
   - Use configurable search count
   - Implement interval-based scheduling
   - Calculate and display API usage projections
   - Track last run date in database
4. **`database.py`** - Added `bot_state` table for tracking scheduling state

## Testing

To test the new configuration:

```bash
# Test with default settings (5 tweets, every 3 days)
python main.py start --dry-run

# Or test a single prayer search
python main.py prayer_search --dry-run
```

The bot will log:
- Current configuration values
- Expected monthly API usage
- Warnings if usage is too high
- When searches actually run (respecting the interval)

## Monitoring

The bot now provides:
- **Startup warnings** if projected usage is too high
- **Actual usage tracking** via `get_actual_usage()` (check with `python main.py status --check-usage`)
- **Database persistence** of last run dates (survives restarts)

## Next Steps

1. **Monitor actual usage** for a few days to verify the projections
2. **Adjust if needed** - if you're using less than expected, you can increase frequency or count
3. **Consider dynamic adjustment** - future enhancement could adjust frequency based on remaining quota

## Notes

- The interval scheduling uses the database to track last run date, so it persists across restarts
- Mentions remain daily (unchanged) - they're more important for direct engagement
- Daily posts don't use API reads (unchanged)
- All changes are backward compatible - if config values aren't set, defaults are used

