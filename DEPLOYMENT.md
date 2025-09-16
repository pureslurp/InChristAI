# InChrist AI - Cloud Deployment Guide

This guide will help you deploy your InChrist AI Twitter bot to various cloud platforms.

## Prerequisites

1. **API Keys Ready**: Have your Twitter API keys and OpenAI API key ready
2. **Git Repository**: Your code should be in a Git repository (GitHub recommended)
3. **Cloud Platform Account**: Choose one of the platforms below

## Deployment Options

### Option 1: Railway.app (Recommended - Easiest)

Railway is the simplest option with automatic deployments and good free tier.

#### Steps:
1. **Sign up**: Go to [railway.app](https://railway.app) and sign up with GitHub
2. **Create Project**: Click "New Project" → "Deploy from GitHub repo"
3. **Select Repository**: Choose your InChristAI repository
4. **Set Environment Variables**: In Railway dashboard, go to "Variables" tab and add:
   ```
   CLOUD_DEPLOYMENT=true
   TWITTER_API_KEY=your_twitter_api_key
   TWITTER_API_SECRET=your_twitter_api_secret
   TWITTER_ACCESS_TOKEN=your_twitter_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
   TWITTER_BEARER_TOKEN=your_twitter_bearer_token
   OPENAI_API_KEY=your_openai_api_key
   BOT_USERNAME=InChristAI
   POSTING_TIME=08:00
   TIMEZONE=America/New_York
   ```
5. **Deploy**: Railway will automatically detect the `railway.toml` and deploy
6. **Add Database** (optional): Add PostgreSQL service for better database support

**Cost**: Free tier includes 500 hours/month, then $5/month

---

### Option 2: Heroku

Heroku is reliable with good documentation and PostgreSQL support.

#### Steps:
1. **Install Heroku CLI**: Download from [heroku.com](https://devcenter.heroku.com/articles/heroku-cli)
2. **Login**: `heroku login`
3. **Create App**:
   ```bash
   cd /path/to/your/InChristAI
   heroku create your-app-name
   ```
4. **Add PostgreSQL**:
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```
5. **Set Environment Variables**:
   ```bash
   heroku config:set CLOUD_DEPLOYMENT=true
   heroku config:set TWITTER_API_KEY=your_twitter_api_key
   heroku config:set TWITTER_API_SECRET=your_twitter_api_secret
   heroku config:set TWITTER_ACCESS_TOKEN=your_twitter_access_token
   heroku config:set TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
   heroku config:set TWITTER_BEARER_TOKEN=your_twitter_bearer_token
   heroku config:set OPENAI_API_KEY=your_openai_api_key
   heroku config:set BOT_USERNAME=InChristAI
   heroku config:set POSTING_TIME=08:00
   heroku config:set TIMEZONE=America/New_York
   ```
6. **Deploy**:
   ```bash
   git add .
   git commit -m "Prepare for Heroku deployment"
   git push heroku main
   ```

**Cost**: Eco dynos start at $5/month, plus $5/month for PostgreSQL

---

### Option 3: DigitalOcean App Platform

Good balance of features and pricing with built-in monitoring.

#### Steps:
1. **Sign up**: Go to [digitalocean.com](https://www.digitalocean.com)
2. **Create App**: Go to Apps → Create App → GitHub
3. **Select Repository**: Choose your InChristAI repository
4. **Configure Build**: DigitalOcean will auto-detect Python
5. **Set Environment Variables**: In App settings, add all the environment variables listed above
6. **Choose Plan**: Basic plan starts at $5/month
7. **Deploy**: Click "Create Resources"

**Cost**: Basic plan $5/month

---

### Option 4: Google Cloud Run

Serverless option that scales to zero when not in use.

#### Steps:
1. **Setup**: Install Google Cloud SDK and authenticate
2. **Enable APIs**:
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```
3. **Build and Deploy**:
   ```bash
   gcloud run deploy inchrist-ai \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="CLOUD_DEPLOYMENT=true,TWITTER_API_KEY=your_key,..."
   ```

**Cost**: Pay per use, very cost-effective for low traffic

---

## Security Setup

### 1. Secure Your Original Config
After deployment, secure your local config file:

```bash
# Backup your original config with credentials
cp config.py config_backup.py

# Replace with environment variable version
cp config_cloud.py config.py
```

### 2. Environment Variables
Never commit API keys to Git. Always use environment variables in production.

### 3. Database Security
For production, use PostgreSQL instead of SQLite:
- More reliable for cloud deployment
- Better concurrent access
- Automatic backups on most platforms

## Monitoring and Maintenance

### Health Checks
All deployments include health check endpoints:
- `https://your-app.com/health` - Basic health check
- `https://your-app.com/status` - Detailed bot status

### Logs
View logs on each platform:
- **Railway**: Dashboard → Deployments → View Logs
- **Heroku**: `heroku logs --tail`
- **DigitalOcean**: App → Runtime Logs
- **Google Cloud**: Cloud Console → Cloud Run → Logs

### Scaling
Most platforms auto-scale, but you can adjust:
- **Railway**: Auto-scales based on usage
- **Heroku**: Scale dynos: `heroku ps:scale worker=1`
- **DigitalOcean**: Adjust in App settings
- **Google Cloud**: Automatic serverless scaling

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Check that `requirements.txt` is up to date
   - Ensure all dependencies are listed

2. **Database connection errors**
   - Make sure `DATABASE_URL` environment variable is set
   - For PostgreSQL, install `psycopg2-binary`

3. **Twitter API failures**
   - Verify all Twitter API environment variables are set
   - Check Twitter API key permissions

4. **Bot not posting**
   - Check logs for scheduling errors
   - Verify timezone settings
   - Ensure worker/dyno is running (not just web)

### Getting Help

1. **Check platform status pages**
2. **Review application logs**
3. **Test locally first**: `python main.py post_verse --dry-run`
4. **Check environment variables**: Ensure all required vars are set

## Cost Optimization

### Railway.app (Recommended for beginners)
- **Free tier**: 500 hours/month
- **Paid**: $5/month for unlimited
- **Database**: Free PostgreSQL included

### Heroku
- **Eco dyno**: $5/month
- **Database**: $5/month for PostgreSQL
- **Total**: ~$10/month

### Cost-saving tips:
1. Use Railway.app free tier initially
2. Monitor usage with platform dashboards
3. Set up billing alerts
4. Consider Google Cloud Run for very low usage

## Next Steps

After deployment:
1. **Test thoroughly**: Verify posting and mention responses work
2. **Set up monitoring**: Check logs regularly first few days
3. **Monitor costs**: Set up billing alerts
4. **Backup database**: Export data periodically
5. **Update dependencies**: Keep libraries updated for security

## Support

- Check the main README.md for application-specific help
- Each cloud platform has extensive documentation
- Test changes locally before deploying to production
