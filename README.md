# 😈 Discord Prank Bot

A Discord bot to send prank messages to your friend's server!

## Features ✨

- **Setup a friend's channel** to send pranks to
- **Send text pranks** directly
- **Send fancy embed pranks** with colors
- Send DMs to your friends
- Keyword auto-responses
- Text formatting commands

## Setup Guide 🚀

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name it (e.g., "Prank Bot")
4. Go to "Bot" section and click "Add Bot"
5. Copy the bot token
6. Go to "OAuth2" > "URL Generator"
7. Select scopes: `bot`
8. Select permissions: `Send Messages`, `Read Messages/View Channels`
9. Copy the generated URL to invite to your server

### 2. Get Your Friend's Channel ID

Ask your friend for their server's channel ID or:
- Enable Developer Mode in Discord (Settings > Advanced > Developer Mode)
- Right-click the channel and click "Copy Channel ID"

### 3. Install & Run

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and add your token
python bot.py
```

### 4. Setup Prank Channel

```
!setup_prank <channel_id> <friend_server_name>
```

Example:
```
!setup_prank 1234567890 JohnServer
```

## Commands 📝

### 😈 Prank Commands (Main Feature!)

| Command | Usage | Description |
|---------|-------|-------------|
| setup_prank | `!setup_prank 1234567890 MyFriend` | Set which channel to prank |
| prank | `!prank EVERYONE READ THIS!` | Send text prank to friend's server |
| prank_embed | `!prank_embed CHECK THIS OUT!` | Send fancy embed prank |
| prank_status | `!prank_status` | Check if prank channel is set |

### 📬 DM Friends

| Command | Usage | Description |
|---------|-------|-------------|
| add_friend | `!add_friend john 123456789` | Add a friend |
| dm_friend | `!dm_friend john Hey there!` | Send DM to one friend |
| dm_all | `!dm_all Join our game!` | Send DM to all friends |

### ✏️ Text Formatting

| Command | Usage | Description |
|---------|-------|-------------|
| uppercase | `!uppercase hello` | Convert to UPPERCASE |
| lowercase | `!lowercase HELLO` | Convert to lowercase |
| reverse | `!reverse hello` | Reverse text |
| spam | `!spam 3 hello` | Repeat text (max 10) |
| echo | `!echo My message` | Echo text |
| embed | `!embed My message` | Send as fancy embed |

### � Send to Channels

| Command | Usage | Description |
|---------|-------|-------------|
| list_channels | `!list_channels` | Show channels in current server |
| send_to_channel | `!send_to_channel 1234567890 Hi!` | Send message to specific channel |
| send_embed_to_channel | `!send_embed_to_channel 1234567890 Hi!` | Send embed to channel |

### 🔑 Keyword Triggers (Auto-Response)

| Command | Usage | Description |
|---------|-------|-------------|
| set_keyword | `!set_keyword hello Hey there!` | Auto-reply when someone says a keyword |
| remove_keyword | `!remove_keyword hello` | Remove a keyword trigger |
| list_keywords | `!list_keywords` | Show all keyword triggers |

**How it works:** When someone mentions a keyword in ANY channel, the bot automatically reacts and sends the response!

## Examples 💬

```
# Setup pranks
!setup_prank 1234567890 FriendsServer

# Send pranks
!prank URGENT: Server maintenance required!
!prank_embed 🚨 CRITICAL SECURITY UPDATE REQUIRED 🚨

# DM friends
!add_friend john 123456789
!dm_all Emergency meeting in 5 minutes!

# Fun stuff
!set_keyword gg Nice game bro!
```

## Security Notes 🔒

- Keep your bot token secret in `.env`
- Only use on servers where you have permission
- It's a **prank** - make sure your friends will find it funny!
- Always get permission before adding bot to a server

## Troubleshooting 🔧

- **Channel not found**: Make sure bot is invited to friend's server
- **No permission**: Bot needs message send permissions
- **Prank not set**: Use `!setup_prank` first
