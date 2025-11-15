# X API Free Tier Optimization Strategies

## Current Situation

**API Limit:** 100 read calls per month

**Current Usage:**
- **Mentions:** 1 call/day = ~30 calls/month ✅
- **Prayer Search:** 10 calls/day (each returned tweet = 1 call) = ~300 calls/month ❌ **WAY OVER LIMIT!**

**Problem:** Each tweet returned from search counts as a separate API call, not just the search request itself.

## Strategy Options

### Strategy 1: Reduce to 5 tweets, run every 3 days (RECOMMENDED)
- **Search:** 5 calls every 3 days = ~50 calls/month
- **Mentions:** ~30 calls/month
- **Total:** ~80 calls/month
- **Buffer:** 20 calls (20% safety margin)
- **Pros:** Safe buffer, maintains diversity (5 tweets), regular engagement
- **Cons:** Less frequent search responses

### Strategy 2: Reduce to 5 tweets, run every other day
- **Search:** 5 calls every 2 days = ~75 calls/month
- **Mentions:** ~30 calls/month
- **Total:** ~105 calls/month
- **Buffer:** -5 calls (slightly over, but manageable)
- **Pros:** More frequent responses, good diversity
- **Cons:** Slightly over limit (may need to skip occasionally)

### Strategy 3: Reduce to 5 tweets, run 3x per week
- **Search:** 5 calls × 3 times/week = ~60 calls/month
- **Mentions:** ~30 calls/month
- **Total:** ~90 calls/month
- **Buffer:** 10 calls (10% safety margin)
- **Pros:** Predictable schedule, good buffer
- **Cons:** Less frequent than daily

### Strategy 4: Reduce to 3 tweets, run every other day
- **Search:** 3 calls every 2 days = ~45 calls/month
- **Mentions:** ~30 calls/month
- **Total:** ~75 calls/month
- **Buffer:** 25 calls (33% safety margin)
- **Pros:** Very safe, frequent responses
- **Cons:** Less diversity (only 3 tweets to choose from)

### Strategy 5: Prioritize mentions, minimal search
- **Search:** 5 calls × 2 times/week = ~40 calls/month
- **Mentions:** ~30 calls/month
- **Total:** ~70 calls/month
- **Buffer:** 30 calls (43% safety margin)
- **Pros:** Maximum safety, prioritizes direct engagement
- **Cons:** Very infrequent search responses

## Recommended Implementation: Strategy 1

**Configuration:**
- Search count: 5 tweets
- Search frequency: Every 3 days
- Mentions: Daily (unchanged)

This provides:
- ✅ Safe 20% buffer
- ✅ Good diversity (5 tweets to choose from)
- ✅ Regular but not excessive search responses
- ✅ Prioritizes mentions (direct engagement)

## Alternative: Dynamic Strategy

You could also implement a dynamic system that:
- Monitors actual API usage throughout the month
- Adjusts frequency based on remaining quota
- Runs more frequently early in the month, conservatively near the end

