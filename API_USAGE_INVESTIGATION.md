# API Usage Investigation Guide

## Problem

You've used 51 API calls in less than a day after your monthly quota reset, but the session counter only shows #22, which suggests the app has been restarting multiple times.

## Key Issue

**The session counter resets on every app restart**, so it only counts calls since the last restart. If your app restarts multiple times, you won't see the full count in the logs.

## Changes Made

### 1. Added Actual Usage Tracking

I've added a `get_actual_usage()` method that queries X API's official usage endpoint to get your **real monthly count** that persists across restarts.

### 2. Improved Logging

- Session counter now clearly labeled as "(session)" to indicate it resets
- Actual monthly usage is checked on startup
- Both session and actual usage shown in status command

### 3. Status Command Updates

Running `python main.py status` now shows both:
- **Session count**: Calls since last restart (resets on restart)
- **Actual monthly count**: Real usage from X API (persists across restarts)

## How to Investigate Your 51 Calls

### Step 1: Check Actual Usage

Run the status command:
```bash
python main.py status
```

Look for the `actual_monthly` section to see your real monthly usage.

### Step 2: Check App Restart History

If you're on Railway or another cloud platform, check:
- **Deployment logs**: How many times has the app restarted?
- **Crash logs**: Has the app been crashing and restarting?
- **Manual restarts**: Have you manually restarted the app?

### Step 3: Review Logs for All API Calls

Search your logs for all `💰 API READ CALL` messages:
```bash
grep "💰 API READ CALL" inchrist_ai.log
```

Count how many times each type appears:
- `get_mentions()` calls
- `search_tweets()` calls
- `get_original_tweet()` calls
- `get_thread_context()` calls

### Step 4: Check Scheduled Tasks

Verify your scheduled tasks are only running once per day:
- **9:00 AM**: `_check_mentions()` - Should make 1 `get_mentions()` call
- **10:00 AM**: `_search_and_respond_to_prayers()` - Should make 1 `search_tweets()` call

### Step 5: Check for Manual Calls

Have you been running any manual commands?
```bash
# These would make API calls:
python main.py check_mentions
python main.py prayer_search
python main.py status  # Now checks actual usage (but that's a read call)
```

### Step 6: Check for Multiple Instances

Are multiple instances of the bot running?
- Multiple Railway deployments?
- Local + cloud instance both running?
- Multiple containers?

## Expected Usage Per Day

With the current setup, you should only make:
- **1 call/day** for mentions (at 9:00 AM)
- **1 call/day** for prayer search (at 10:00 AM)
- **Total: 2 calls/day = ~60 calls/month**

## Common Causes of High Usage

1. **App restarts frequently** - Each restart may trigger calls during initialization
2. **Multiple instances running** - Duplicate deployments making duplicate calls
3. **Scheduled tasks running multiple times** - Timezone issues or duplicate schedules
4. **Manual testing** - Running commands manually adds to the count
5. **Database resets** - If database resets, mentions check might process old mentions again

## Next Steps

1. **Enable startup logging** - The app now logs actual usage on startup
2. **Monitor for a few days** - Check logs daily to see usage patterns
3. **Check Railway logs** - Look for restart patterns
4. **Use the status command** - Run it daily to track actual usage

## New Features

### Check Actual Usage Programmatically

```python
from twitter_api import TwitterAPI

api = TwitterAPI()
usage = api.get_actual_usage()
print(f"Monthly usage: {usage.get('monthly_used', 'unknown')}/{usage.get('monthly_limit', 100)}")
```

### Check Status with Actual Usage

```bash
python main.py status
```

This will show both session and actual monthly usage.

## Important Notes

- The **session counter** (what you see in logs) resets on every restart
- The **actual monthly usage** from X API is the real count you should monitor
- The `get_actual_usage()` method makes a call to the usage endpoint, but this typically doesn't count against your read limit (it's a usage check, not a data retrieval)
- If you see high usage, check for multiple restarts or multiple instances running

