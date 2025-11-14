# X API Read Call Usage Analysis

## Problem Summary

The application was exhausting the 100 monthly X API read calls very quickly (after just 2 search function calls). This document explains what was happening and how it was fixed.

## Understanding X API Read Calls

On the X API Free tier, you get **100 read operations per month**. The following operations count as **READ** calls:

1. `GET /2/tweets/search/recent` - Search for tweets
2. `GET /2/users/{id}/mentions` - Get mentions
3. `GET /2/tweets/{id}` - Get a specific tweet
4. Any GET request to retrieve data

**Note**: POST operations (like posting tweets, replies) do NOT count as reads.

## The Problem: Hidden API Calls

### Expected Usage
The application was designed to make:
- **1 call/day** to `get_mentions()` = ~30 calls/month
- **1 call/day** to `search_tweets()` for prayer search = ~30 calls/month
- **Total expected**: ~60 calls/month (with 40 call buffer)

### Actual Usage (The Bug)

However, there was a hidden cost in `interaction_handler.py`:

#### The Expensive Check
In `_has_responded_to_tweet()`, for every mention without a database record, the code was making an additional API call to verify via Twitter:

```python
def _check_twitter_for_our_reply(self, tweet_id: str) -> bool:
    search_query = f"in_reply_to_tweet_id:{tweet_id} from:{bot_username}"
    search_results = self.twitter_api.search_tweets(search_query, count=10)  # READ CALL!
```

#### Why This Was Expensive

When processing mentions:
1. `get_mentions()` returns 25 mentions = **1 API call**
2. For each mention, `_has_responded_to_tweet()` is called
3. If database check fails (e.g., after deployment/reset), it calls `_check_twitter_for_our_reply()`
4. This makes a `search_tweets()` call = **1 API call per mention**

**Result**: If you have 50 mentions without database records, that's:
- 1 call for `get_mentions()`
- 50 calls for checking each mention
- **Total: 51 API calls in one run!**

After 2 runs, you'd exceed the 100 call monthly limit.

## The Fix

Removed the Twitter API verification fallback and made the database the single source of truth:

1. **Removed** `_check_twitter_for_our_reply()` method entirely
2. **Updated** `_has_responded_to_tweet()` to only check the database
3. **Added warnings** in code comments to prevent re-adding expensive checks

### After Fix Usage

Now the application only makes:
- **1 call/day** to `get_mentions()` = ~30 calls/month
- **1 call/day** to `search_tweets()` for prayer search = ~30 calls/month
- **Total: ~60 calls/month** (well within the 100 call limit)

## Monitoring API Usage

The code includes logging for every API call:

- `💰 API CALL MADE: get_mentions()` - Logged in `twitter_api.py`
- `💰 API CALL MADE: search_tweets(...)` - Logged in `twitter_api.py`
- Rate limit headers are also logged showing remaining calls

Check your logs for these messages to monitor actual usage.

## Best Practices Going Forward

1. **Never add API verification as a fallback** - Database is the source of truth
2. **Always check the database first** before making API calls
3. **Use `since_id` parameter** in `get_mentions()` to avoid redundant calls (already implemented)
4. **Monitor logs** for the `💰 API CALL MADE` messages
5. **Test with dry-run mode** first before deploying changes

## Scheduled Tasks and API Usage

Current scheduled tasks:
- **Daily mentions check** at 9:00 AM: 1 `get_mentions()` call = ~30/month
- **Daily prayer search** at 10:00 AM: 1 `search_tweets()` call = ~30/month
- **Daily verse posting**: No read calls (only POST operations)

## Database as Source of Truth

The database (`interactions` table) now serves as the single source of truth for:
- Which tweets we've responded to
- Interaction history
- User information

If the database is reset:
- The application will re-process mentions from the last `get_mentions()` call
- It may respond to tweets it has already responded to
- This is acceptable to preserve the API quota

## Testing Changes

Before deploying any changes that might affect API usage:
1. Run with `--dry-run` flag to test without making API calls
2. Check logs for `💰 API CALL MADE` messages
3. Count expected API calls before deployment
4. Monitor usage after deployment

