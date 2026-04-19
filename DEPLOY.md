# Deploy to Railway 🚂

Easy steps to deploy your Discord bot to Railway!

## Prerequisites

1. **GitHub Account** - Create one at github.com
2. **Railway Account** - Create one at railway.app (free tier available)
3. **Discord Bot Token** - You already have this!

## Step-by-Step Deployment

### 1. Push Code to GitHub

```powershell
# Initialize git repo
git init
git add .
git commit -m "Initial commit: Prank bot"

# Create new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/discord-prank-bot.git
git branch -M main
git push -u origin main
```

### 2. Connect Railway to GitHub

1. Go to [railway.app](https://railway.app)
2. Sign up/Login
3. Click "New Project" → "Deploy from GitHub Repo"
4. Authorize Railway to access GitHub
5. Select your `discord-prank-bot` repo
6. Click "Deploy Now"

### 3. Add Environment Variables

In Railway Dashboard:
1. Go to your project
2. Click "Variables"
3. Add:
   - **DISCORD_TOKEN** = your bot token (from Discord Developer Portal)
   - **COMMAND_PREFIX** = !

### 4. Monitor & Restart

- Railway will automatically start your bot
- View logs: Click your project → "Logs" tab
- Bot runs 24/7! ✅

## What Files Does Railway Need?

✅ `Procfile` - Tells Railway how to run the bot
✅ `Dockerfile` - Alternative: Docker container setup
✅ `requirements.txt` - Python dependencies
✅ `bot.py` - Main bot code
✅ `friends_config.json` - Config file

## Troubleshooting

**Bot not starting:**
- Check `DISCORD_TOKEN` is set in Railway Variables
- View logs for error messages

**"Module not found" error:**
- Make sure `requirements.txt` has all imports
- Run: `pip freeze > requirements.txt`

**Bot disconnects:**
- Railway might be restarting it
- Check logs for the issue

## Free Tier Limits

- ✅ 500 hours/month (plenty for 24/7 bot!)
- ✅ No credit card required
- ✅ Paid plans available for more

## Keep Bot Running 24/7

Railway keeps your bot running automatically!
- No need to run `python bot.py` on your PC
- Bot is always online
- Restarts automatically if it crashes

## Updates

To update your bot:
1. Make changes locally
2. `git add . && git commit -m "Update"` 
3. `git push`
4. Railway auto-deploys! 🚀

## Need Help?

- Railway Docs: https://docs.railway.app
- Discord.py Docs: https://discordpy.readthedocs.io
- Railway Community: https://railway.app/support
