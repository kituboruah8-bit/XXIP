import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')

# Create bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.guilds = True
intents.guild_messages = True
intents.members = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Load friends configuration
def load_friends_config():
    """Load friends and messages from JSON file"""
    try:
        with open('friends_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("friends_config.json not found. Creating default...")
        default_config = {
            "friends": {},
            "messages": {
                "default": "Hey! Join us for something fun!"
            }
        }
        with open('friends_config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config

def save_friends_config(config):
    """Save friends configuration to JSON file"""
    with open('friends_config.json', 'w') as f:
        json.dump(config, f, indent=2)

@bot.event
async def on_ready():
    """Called when bot connects to Discord"""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is ready to use. Use {COMMAND_PREFIX}help for commands.')

@bot.event
async def on_message(message):
    """Handle messages in channels and DMs"""
    # Don't respond to ourselves
    if message.author == bot.user:
        return
    
    # Load config for keyword responses
    config = load_friends_config()
    
    # Check for keyword triggers in any channel/DM
    if 'keywords' in config:
        for keyword, response in config['keywords'].items():
            if keyword.lower() in message.content.lower():
                # Add reaction
                try:
                    await message.add_reaction('👀')
                except:
                    pass
                # Send response
                await message.reply(response, mention_author=False)
                break
    
    # Process commands
    await bot.process_commands(message)

@bot.command(name='add_friend')
async def add_friend(ctx, name: str, user_id: int):
    """Add a friend to the friends list
    Usage: !add_friend john 123456789
    """
    config = load_friends_config()
    config['friends'][name] = user_id
    save_friends_config(config)
    await ctx.send(f'✅ Added {name} (ID: {user_id}) to friends list!')

@bot.command(name='remove_friend')
async def remove_friend(ctx, name: str):
    """Remove a friend from the friends list
    Usage: !remove_friend john
    """
    config = load_friends_config()
    if name in config['friends']:
        del config['friends'][name]
        save_friends_config(config)
        await ctx.send(f'✅ Removed {name} from friends list!')
    else:
        await ctx.send(f'❌ Friend "{name}" not found!')

@bot.command(name='list_friends')
async def list_friends(ctx):
    """List all friends"""
    config = load_friends_config()
    if not config['friends']:
        await ctx.send('No friends added yet. Use !add_friend to add some!')
        return
    
    embed = discord.Embed(title="📋 Your Friends", color=discord.Color.blue())
    for name, user_id in config['friends'].items():
        embed.add_field(name=name, value=f"ID: {user_id}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='dm_friend')
async def dm_friend(ctx, friend_name: str, *, message: str):
    """Send a DM to a specific friend
    Usage: !dm_friend john Hey, join our game!
    """
    config = load_friends_config()
    
    if friend_name not in config['friends']:
        await ctx.send(f'❌ Friend "{friend_name}" not found! Use !list_friends to see all friends.')
        return
    
    user_id = config['friends'][friend_name]
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        await ctx.send(f'✅ Message sent to {friend_name}!')
    except discord.NotFound:
        await ctx.send(f'❌ Could not find Discord user with ID {user_id}')
    except discord.Forbidden:
        await ctx.send(f'❌ Cannot send DM to {friend_name} (they may have DMs disabled)')
    except Exception as e:
        await ctx.send(f'❌ Error sending message: {str(e)}')

@bot.command(name='dm_all')
async def dm_all(ctx, *, message: str):
    """Send a DM to all friends
    Usage: !dm_all Join our new event!
    """
    config = load_friends_config()
    
    if not config['friends']:
        await ctx.send('No friends added yet!')
        return
    
    success_count = 0
    failed_count = 0
    failed_friends = []
    
    embed = discord.Embed(title="📨 Sending Messages...", color=discord.Color.gold())
    
    for friend_name, user_id in config['friends'].items():
        try:
            user = await bot.fetch_user(user_id)
            await user.send(message)
            success_count += 1
        except discord.NotFound:
            failed_count += 1
            failed_friends.append(f"{friend_name} (User not found)")
        except discord.Forbidden:
            failed_count += 1
            failed_friends.append(f"{friend_name} (DMs disabled)")
        except Exception as e:
            failed_count += 1
            failed_friends.append(f"{friend_name} ({str(e)})")
    
    embed.add_field(name="✅ Sent", value=f"{success_count} message(s)", inline=False)
    if failed_friends:
        embed.add_field(name="❌ Failed", value="\n".join(failed_friends), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='save_message')
async def save_message(ctx, message_name: str, *, message_text: str):
    """Save a message template for later use
    Usage: !save_message event_invite Join our gaming session tonight!
    """
    config = load_friends_config()
    config['messages'][message_name] = message_text
    save_friends_config(config)
    await ctx.send(f'✅ Message "{message_name}" saved!')

@bot.command(name='list_messages')
async def list_messages(ctx):
    """List all saved messages"""
    config = load_friends_config()
    if not config['messages']:
        await ctx.send('No messages saved yet!')
        return
    
    embed = discord.Embed(title="📝 Saved Messages", color=discord.Color.green())
    for name, text in config['messages'].items():
        embed.add_field(name=name, value=text, inline=False)
    await ctx.send(embed=embed)

@bot.command(name='dm_with_template')
async def dm_with_template(ctx, friend_name: str, message_name: str):
    """Send a saved message template to a friend
    Usage: !dm_with_template john event_invite
    """
    config = load_friends_config()
    
    if message_name not in config['messages']:
        await ctx.send(f'❌ Message template "{message_name}" not found!')
        return
    
    if friend_name not in config['friends']:
        await ctx.send(f'❌ Friend "{friend_name}" not found!')
        return
    
    message = config['messages'][message_name]
    user_id = config['friends'][friend_name]
    
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        await ctx.send(f'✅ Message sent to {friend_name}!')
    except Exception as e:
        await ctx.send(f'❌ Error: {str(e)}')

@bot.command(name='uppercase')
async def uppercase(ctx, *, text: str):
    """Convert text to UPPERCASE
    Usage: !uppercase hello world
    """
    await ctx.send(f"📤 {text.upper()}")

@bot.command(name='lowercase')
async def lowercase(ctx, *, text: str):
    """Convert text to lowercase
    Usage: !lowercase HELLO WORLD
    """
    await ctx.send(f"📥 {text.lower()}")

@bot.command(name='reverse')
async def reverse(ctx, *, text: str):
    """Reverse text
    Usage: !reverse hello
    """
    await ctx.send(f"🔄 {text[::-1]}")

@bot.command(name='spam')
async def spam(ctx, count: int, *, text: str):
    """Repeat text multiple times (max 10)
    Usage: !spam 3 hello
    """
    if count > 10:
        count = 10
    if count < 1:
        count = 1
    
    message = " ".join([text] * count)
    await ctx.send(message)

@bot.command(name='react_to')
async def react_to(ctx, emoji: str, *, message_id_or_text: str):
    """React to a message with emoji
    Usage: !react_to 👍 123456789 (message ID)
    """
    try:
        msg_id = int(message_id_or_text)
        message = await ctx.fetch_message(msg_id)
        await message.add_reaction(emoji)
        await ctx.send(f"✅ Added reaction {emoji} to message!")
    except ValueError:
        await ctx.send("❌ Invalid message ID!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='set_keyword')
async def set_keyword(ctx, keyword: str, *, response: str):
    """Set a keyword trigger for auto-response
    Usage: !set_keyword hello Hey there!
    """
    config = load_friends_config()
    if 'keywords' not in config:
        config['keywords'] = {}
    
    config['keywords'][keyword.lower()] = response
    save_friends_config(config)
    await ctx.send(f'✅ Set keyword "{keyword}" → "{response}"')

@bot.command(name='remove_keyword')
async def remove_keyword(ctx, keyword: str):
    """Remove a keyword trigger
    Usage: !remove_keyword hello
    """
    config = load_friends_config()
    if 'keywords' in config and keyword.lower() in config['keywords']:
        del config['keywords'][keyword.lower()]
        save_friends_config(config)
        await ctx.send(f'✅ Removed keyword "{keyword}"')
    else:
        await ctx.send(f'❌ Keyword "{keyword}" not found!')

@bot.command(name='list_keywords')
async def list_keywords(ctx):
    """List all keyword triggers"""
    config = load_friends_config()
    if 'keywords' not in config or not config['keywords']:
        await ctx.send('No keywords set yet!')
        return
    
    embed = discord.Embed(title="🔑 Keyword Triggers", color=discord.Color.green())
    for keyword, response in config['keywords'].items():
        embed.add_field(name=keyword, value=response, inline=False)
    await ctx.send(embed=embed)

@bot.command(name='echo')
async def echo(ctx, *, text: str):
    """Echo text in the channel
    Usage: !echo Hello everyone!
    """
    await ctx.send(text)

@bot.command(name='embed')
async def embed(ctx, *, text: str):
    """Send text as a nice embed
    Usage: !embed My message here
    """
    embed = discord.Embed(description=text, color=discord.Color.random())
    await ctx.send(embed=embed)

@bot.command(name='announce')
async def announce(ctx, *, text: str):
    """Send an announcement embed to the channel
    Usage: !announce Server maintenance at 10 PM
    """
    embed = discord.Embed(title="📢 ANNOUNCEMENT", description=text, color=discord.Color.red())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    embed.set_footer(text=f"Posted at {ctx.message.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    await ctx.send(embed=embed)

@bot.command(name='poll')
async def poll(ctx, question: str, *options):
    """Create a poll with reactions
    Usage: !poll "Favorite color?" 🔴 🟢 🔵
    """
    if len(options) < 2:
        await ctx.send("❌ Need at least 2 options!")
        return
    
    if len(options) > 10:
        await ctx.send("❌ Maximum 10 options!")
        return
    
    embed = discord.Embed(title="📊 POLL", description=question, color=discord.Color.purple())
    for i, option in enumerate(options, 1):
        embed.add_field(name=f"Option {i}", value=option, inline=False)
    
    msg = await ctx.send(embed=embed)
    for option in options:
        await msg.add_reaction(option)

@bot.command(name='clear')
async def clear(ctx, amount: int = 10):
    """Delete recent messages (max 100, mod only)
    Usage: !clear 5
    """
    if amount > 100:
        amount = 100
    
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("❌ You need manage messages permission!")
        return
    
    try:
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"✅ Deleted {len(deleted)} messages!", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='info')
async def info(ctx):
    """Show server and user info
    Usage: !info
    """
    embed = discord.Embed(title="ℹ️ Server Info", color=discord.Color.blue())
    embed.add_field(name="Server Name", value=ctx.guild.name, inline=False)
    embed.add_field(name="Members", value=ctx.guild.member_count, inline=False)
    embed.add_field(name="Created", value=ctx.guild.created_at.strftime('%Y-%m-%d'), inline=False)
    embed.add_field(name="You", value=ctx.author.name, inline=False)
    embed.set_thumbnail(url=ctx.guild.icon.url)
    await ctx.send(embed=embed)

@bot.command(name='avatar')
async def avatar(ctx, user: discord.User = None):
    """Show user avatar
    Usage: !avatar @user (or just !avatar for yourself)
    """
    user = user or ctx.author
    embed = discord.Embed(title=f"{user.name}'s Avatar", color=discord.Color.blurple())
    embed.set_image(url=user.avatar.url)
    await ctx.send(embed=embed)

@bot.command(name='list_channels')
async def list_channels(ctx):
    """List all channels in the server that bot can access
    Usage: !list_channels
    """
    if not ctx.guild:
        await ctx.send("❌ This command only works in servers!")
        return
    
    channels = ctx.guild.text_channels
    embed = discord.Embed(title="📋 Server Channels", color=discord.Color.blue())
    
    channel_list = []
    for channel in channels:
        try:
            # Check if bot can send messages
            perms = channel.permissions_for(ctx.guild.me)
            if perms.send_messages:
                channel_list.append(f"✅ {channel.name} (ID: {channel.id})")
            else:
                channel_list.append(f"❌ {channel.name} (No access)")
        except:
            channel_list.append(f"❌ {channel.name} (Error checking)")
    
    # Split into chunks if too many
    for i in range(0, len(channel_list), 10):
        chunk = channel_list[i:i+10]
        if i == 0:
            embed.add_field(name="Channels", value="\n".join(chunk), inline=False)
        else:
            embed2 = discord.Embed(color=discord.Color.blue())
            embed2.add_field(name="More Channels", value="\n".join(chunk), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='setup_prank')
async def setup_prank(ctx, channel_id: int, server_name: str = "Friend's Server"):
    """Setup which channel to prank (must be in a server bot can access)
    Usage: !setup_prank 1234567890 MyFriendServer
    """
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            await ctx.send(f"❌ Channel with ID {channel_id} not found! Make sure bot is invited to that server.")
            return
        
        perms = channel.permissions_for(channel.guild.me)
        if not perms.send_messages:
            await ctx.send(f"❌ I don't have permission to send messages in {channel.mention}")
            return
        
        config = load_friends_config()
        config['prank_config']['friend_server_channel_id'] = channel_id
        config['prank_config']['friend_server_name'] = server_name
        save_friends_config(config)
        
        embed = discord.Embed(title="✅ Prank Channel Set!", color=discord.Color.green())
        embed.add_field(name="Channel", value=f"{channel.mention}", inline=False)
        embed.add_field(name="Server", value=server_name, inline=False)
        embed.add_field(name="Tip", value="Now use !prank or !prank_embed to send messages!", inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='prank')
async def prank(ctx, *, message: str):
    """Send a prank message to friend's server
    Usage: !prank EVERYONE NEEDS TO READ THIS!
    """
    config = load_friends_config()
    channel_id = config.get('prank_config', {}).get('friend_server_channel_id', 0)
    
    if channel_id == 0:
        await ctx.send("❌ Prank channel not set! Use !setup_prank first!")
        return
    
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            await ctx.send("❌ Prank channel not found! Use !setup_prank again.")
            return
        
        await channel.send(message)
        await ctx.send(f"😈 Prank sent to **{config['prank_config']['friend_server_name']}**! 🤣")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='prank_embed')
async def prank_embed(ctx, *, message: str):
    """Send a fancy prank embed to friend's server
    Usage: !prank_embed Check out this cool announcement!
    """
    config = load_friends_config()
    channel_id = config.get('prank_config', {}).get('friend_server_channel_id', 0)
    
    if channel_id == 0:
        await ctx.send("❌ Prank channel not set! Use !setup_prank first!")
        return
    
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            await ctx.send("❌ Prank channel not found! Use !setup_prank again.")
            return
        
        embed = discord.Embed(description=message, color=discord.Color.red())
        embed.set_footer(text="This is a prank! 😜")
        await channel.send(embed=embed)
        await ctx.send(f"😈 Prank embed sent to **{config['prank_config']['friend_server_name']}**! 🤣")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='prank_status')
async def prank_status(ctx):
    """Check if prank channel is configured
    Usage: !prank_status
    """
    config = load_friends_config()
    channel_id = config.get('prank_config', {}).get('friend_server_channel_id', 0)
    server_name = config.get('prank_config', {}).get('friend_server_name', '')
    
    if channel_id == 0 or not server_name:
        await ctx.send("❌ Prank channel not set! Use !setup_prank first!")
        return
    
    embed = discord.Embed(title="😈 Prank Status", color=discord.Color.orange())
    embed.add_field(name="Server", value=server_name, inline=False)
    embed.add_field(name="Channel ID", value=channel_id, inline=False)
    embed.add_field(name="Ready to Prank?", value="✅ YES! Use !prank or !prank_embed", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='send_to_channel')
async def send_to_channel(ctx, channel_id: int, *, message: str):
    """Send a message to a specific channel (friend's server)
    Usage: !send_to_channel 1234567890 Hello everyone!
    """
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            await ctx.send(f"❌ Channel with ID {channel_id} not found!")
            return
        
        # Check permissions
        perms = channel.permissions_for(channel.guild.me)
        if not perms.send_messages:
            await ctx.send(f"❌ I don't have permission to send messages in {channel.mention}")
            return
        
        await channel.send(message)
        await ctx.send(f"✅ Message sent to {channel.mention} in **{channel.guild.name}**!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='send_embed_to_channel')
async def send_embed_to_channel(ctx, channel_id: int, *, message: str):
    """Send a formatted embed to a specific channel (friend's server)
    Usage: !send_embed_to_channel 1234567890 Hello everyone!
    """
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            await ctx.send(f"❌ Channel with ID {channel_id} not found!")
            return
        
        perms = channel.permissions_for(channel.guild.me)
        if not perms.send_messages:
            await ctx.send(f"❌ I don't have permission to send messages in {channel.mention}")
            return
        
        embed = discord.Embed(description=message, color=discord.Color.random())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        await channel.send(embed=embed)
        await ctx.send(f"✅ Embed sent to {channel.mention} in **{channel.guild.name}**!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='broadcast')
async def broadcast(ctx, *, message: str):
    """Send a message to ALL channels in the server (admin only)
    Usage: !broadcast Important announcement!
    """
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ You need administrator permission!")
        return
    
    if not ctx.guild:
        await ctx.send("❌ This command only works in servers!")
        return
    
    channels = ctx.guild.text_channels
    success = 0
    failed = 0
    
    for channel in channels:
        try:
            perms = channel.permissions_for(ctx.guild.me)
            if perms.send_messages:
                await channel.send(message)
                success += 1
            else:
                failed += 1
        except:
            failed += 1
    
    embed = discord.Embed(title="📢 Broadcast Complete", color=discord.Color.green())
    embed.add_field(name="✅ Sent To", value=f"{success} channels", inline=True)
    embed.add_field(name="❌ Failed", value=f"{failed} channels", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='help_bot')
async def help_bot(ctx):
    """Show all available commands"""
    embed = discord.Embed(title="🤖 Bot Help - Page 1", color=discord.Color.blurple())
    embed.add_field(name="� Prank Commands", value="`!setup_prank` `!prank` `!prank_embed` `!prank_status`", inline=False)
    
    embed.add_field(name="📬 DM Friends", value="`!add_friend` `!remove_friend` `!list_friends` `!dm_friend` `!dm_all`", inline=False)
    
    embed.add_field(name="✏️ Text Features", value="`!uppercase` `!lowercase` `!reverse` `!spam` `!echo` `!embed`", inline=False)
    
    embed.add_field(name="📨 Send Messages", value="`!list_channels` `!send_to_channel` `!send_embed_to_channel`", inline=False)
    
    embed.add_field(name="�🔑 Keyword Triggers", value="`!set_keyword` `!remove_keyword` `!list_keywords`", inline=False)
    
    embed.add_field(name="🛠️ Moderation", value="`!clear`", inline=False)
    
    embed.set_footer(text="Use !prank and !prank_embed for the best pranks!")
    
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not set! Please create a .env file with your bot token.")
        print("See .env.example for the format.")
    else:
        bot.run(DISCORD_TOKEN)
