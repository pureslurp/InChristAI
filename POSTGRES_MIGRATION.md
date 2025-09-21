# PostgreSQL Migration Guide

## 🎯 Overview

This guide helps you migrate your InChristAI bot from SQLite (ephemeral) to PostgreSQL (persistent) on Railway. This will prevent data loss on deployments and provide better performance.

## 🚀 Quick Setup

### Step 1: Add PostgreSQL Service in Railway

1. **Go to your Railway dashboard**
2. **Select your InChristAI project**
3. **Click "New Service"**
4. **Choose "Database" → "PostgreSQL"**
5. **Railway will automatically provision a PostgreSQL database**

### Step 2: Get Database Connection Details

1. **Click on the PostgreSQL service**
2. **Go to "Variables" tab**
3. **Copy the `DATABASE_URL`** (looks like: `postgresql://username:password@host:port/database`)

### Step 3: Set Environment Variable

In your Railway project settings, add:
```
DATABASE_URL=postgresql://username:password@host:port/database
```

### Step 4: Deploy

1. **Commit your changes**
2. **Push to your repository**
3. **Railway will automatically redeploy**
4. **Check logs** to ensure PostgreSQL connection works

## 🔧 What Changed

### New Files
- `database.py` - Database abstraction layer supporting both SQLite and PostgreSQL
- `test_database.py` - Test script to verify database functionality

### Updated Files
- `interaction_handler.py` - Now uses DatabaseManager instead of direct SQLite
- `daily_poster.py` - Updated to use DatabaseManager
- `main.py` - Updated database checks to use DatabaseManager

### Key Features
- **Automatic detection** - Uses PostgreSQL if `DATABASE_URL` starts with `postgresql://`, otherwise uses SQLite
- **Backward compatibility** - Still works with SQLite for local development
- **Connection pooling** - Proper connection management with context managers
- **Error handling** - Graceful fallbacks and detailed logging

## 🧪 Testing

Run the test script to verify everything works:

```bash
python test_database.py
```

This will test both SQLite and PostgreSQL (if configured).

## 📊 Benefits After Migration

✅ **Persistent data** - No more data loss on deployments  
✅ **Better performance** - PostgreSQL is faster than SQLite  
✅ **Automatic backups** - Railway handles backups  
✅ **Scalability** - Can handle more concurrent users  
✅ **Professional setup** - Production-ready database  

## 🔄 Migration Process

### Current State (SQLite)
- Database file: `inchrist_ai.db`
- Location: Container filesystem (ephemeral)
- **Problem**: Wiped on every deployment

### New State (PostgreSQL)
- Database: Railway PostgreSQL service
- Location: Persistent cloud database
- **Benefit**: Data survives deployments

### Data Migration
- **Existing data**: Will be lost (this is expected for the first deployment)
- **New data**: Will persist across all future deployments
- **Rate limiting**: Will work properly (no more duplicate responses)
- **User tracking**: Will maintain history

## 🛠️ Troubleshooting

### Connection Issues
```bash
# Check if DATABASE_URL is set
echo $DATABASE_URL

# Test database connection
python test_database.py
```

### Common Issues
1. **Missing psycopg2**: Already included in `requirements.txt`
2. **Wrong DATABASE_URL format**: Should start with `postgresql://`
3. **Permission issues**: Railway handles this automatically

### Logs to Check
Look for these log messages:
- `PostgreSQL connection configured for host:port/database`
- `Database tables initialized successfully`
- `Added original tweet context from mention data`

## 🔒 Security Notes

- **DATABASE_URL** contains credentials - keep it secure
- **Railway** automatically rotates credentials
- **Connection** uses SSL by default
- **No manual credential management** needed

## 📈 Performance

### Before (SQLite)
- File-based database
- Single connection
- Local storage only

### After (PostgreSQL)
- Network database
- Connection pooling
- Optimized queries with indexes
- Better concurrent access

## 🎉 Success Indicators

You'll know the migration worked when:
1. **Bot starts successfully** with PostgreSQL logs
2. **Data persists** between deployments
3. **No duplicate responses** to mentions
4. **Rate limiting works** properly
5. **Statistics are maintained** across restarts

## 📞 Support

If you encounter issues:
1. Check Railway logs for database connection errors
2. Verify `DATABASE_URL` is correctly set
3. Run `python test_database.py` for diagnostics
4. Check that `psycopg2-binary` is installed (already in requirements.txt)

---

**🎯 Result**: Your bot will now have persistent data storage and won't lose information on deployments!
