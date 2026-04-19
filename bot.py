import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Create bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.guilds = True
intents.guild_messages = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="", intents=intents)

# Track voice channels bot should stay in
voice_channels_to_keep = {}  # {guild_id: channel_id}

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
            },
            "keywords": {},
            "prank_config": {
                "friend_server_channel_id": 0,
                "friend_server_name": ""
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
    print(f'Bot is ready! Using slash commands (/) instead of prefix commands.')
    print(f"Commands in tree: {len(bot.tree._get_all_commands())}")
    
    # Start the voice channel keep-alive task
    keep_bot_in_vc.start()
    
    # Sync with a small delay to ensure bot is fully ready
    import asyncio
    await asyncio.sleep(1)
    
    try:
        # Sync to all guilds (servers) where bot is a member
        synced_count = 0
        for guild in bot.guilds:
            try:
                synced = await bot.tree.sync(guild=guild)
                synced_count += len(synced)
                print(f"✅ Synced {len(synced)} command(s) to guild: {guild.name}")
            except Exception as e:
                print(f"❌ Error syncing to {guild.name}: {e}")
        
        print(f"✅ Total: {synced_count} command(s) synced!")
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()

@tasks.loop(seconds=30)
async def keep_bot_in_vc():
    """Background task to keep bot connected to voice channels"""
    for guild_id, channel_id in list(voice_channels_to_keep.items()):
        try:
            # Find the guild and channel
            guild = bot.get_guild(guild_id)
            if not guild:
                del voice_channels_to_keep[guild_id]
                continue
            
            # Check if bot is already connected to the right channel
            if guild.voice_client and guild.voice_client.channel.id == channel_id:
                # Already connected to correct channel
                continue
            
            # Bot is either not connected or in wrong channel - reconnect
            channel = guild.get_channel(channel_id)
            if not channel:
                print(f"⚠️ Channel {channel_id} not found in {guild.name}")
                del voice_channels_to_keep[guild_id]
                continue
            
            # Disconnect from any current connection
            if guild.voice_client:
                try:
                    await guild.voice_client.disconnect(force=True)
                except:
                    pass
                import asyncio
                await asyncio.sleep(1)
            
            # Try to reconnect
            try:
                await channel.connect()
                print(f"🔄 [Keep-alive] Reconnected to {channel.name} in {guild.name}")
            except Exception as e:
                print(f"❌ [Keep-alive] Failed to reconnect to {channel.name}: {e}")
        
        except Exception as e:
            print(f"❌ [Keep-alive] Error: {e}")

@bot.event
async def on_message(message):
    """Handle messages for keyword triggers"""
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

@bot.event
async def on_voice_state_update(member, before, after):
    """Handle when bot is kicked from voice channel or disconnects"""
    if member == bot.user:
        if before.channel and not after.channel:
            print(f"📴 Bot disconnected from {before.channel.name}")
            # Auto-rejoin if we should stay in this channel
            guild_id = member.guild.id
            if guild_id in voice_channels_to_keep:
                print(f"🔄 Auto-rejoining {before.channel.name}...")
                import asyncio
                await asyncio.sleep(2)
                try:
                    channel = member.guild.get_channel(voice_channels_to_keep[guild_id])
                    if channel:
                        await channel.connect()
                        print(f"✅ Auto-rejoined {channel.name}")
                except Exception as e:
                    print(f"❌ Failed to auto-rejoin: {e}")
        elif after.channel and not before.channel:
            print(f"🔊 Bot connected to {after.channel.name}")
        elif before.channel != after.channel and after.channel:
            print(f"🔄 Bot moved from {before.channel.name} to {after.channel.name}")

@bot.tree.command(name="add_friend", description="Add a friend to the friends list")
@app_commands.describe(
    name="Friend's name (for reference)",
    user_id="Their Discord user ID"
)
async def add_friend(interaction: discord.Interaction, name: str, user_id: int):
    config = load_friends_config()
    config['friends'][name] = user_id
    save_friends_config(config)
    await interaction.response.send_message(f'✅ Added {name} (ID: {user_id}) to friends list!')

@bot.tree.command(name="remove_friend", description="Remove a friend from the friends list")
@app_commands.describe(name="Friend's name to remove")
async def remove_friend(interaction: discord.Interaction, name: str):
    config = load_friends_config()
    if name in config['friends']:
        del config['friends'][name]
        save_friends_config(config)
        await interaction.response.send_message(f'✅ Removed {name} from friends list!')
    else:
        await interaction.response.send_message(f'❌ Friend "{name}" not found!')

@bot.tree.command(name="list_friends", description="List all friends")
async def list_friends(interaction: discord.Interaction):
    config = load_friends_config()
    if not config['friends']:
        await interaction.response.send_message('No friends added yet. Use /add_friend to add some!')
        return
    
    embed = discord.Embed(title="📋 Your Friends", color=discord.Color.blue())
    for name, user_id in config['friends'].items():
        embed.add_field(name=name, value=f"ID: {user_id}", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="dm_friend", description="Send a DM to a specific friend")
@app_commands.describe(
    friend_name="Friend's name (must be added first)",
    message="Message to send"
)
async def dm_friend(interaction: discord.Interaction, friend_name: str, message: str):
    config = load_friends_config()
    
    if friend_name not in config['friends']:
        await interaction.response.send_message(f'❌ Friend "{friend_name}" not found!\nUse `/list_friends` to see available friends')
        return
    
    user_id = config['friends'][friend_name]
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        embed = discord.Embed(title="✅ DM Sent!", description=f"Message sent to **{friend_name}**", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    except discord.NotFound:
        await interaction.response.send_message(f'❌ Error: User with ID {user_id} not found. They may have deleted their account.')
    except discord.Forbidden:
        await interaction.response.send_message(f'🔒 **DMs Disabled**: {friend_name} has DMs turned OFF.\n\nAsk them to enable DMs in Settings → Privacy & Safety → Allow Direct Messages')
    except Exception as e:
        await interaction.response.send_message(f'❌ Error: {str(e)}')

@bot.tree.command(name="dm_all", description="Send a DM to all friends")
@app_commands.describe(message="Message to send to all friends")
async def dm_all(interaction: discord.Interaction, message: str):
    config = load_friends_config()
    
    if not config['friends']:
        await interaction.response.send_message('❌ No friends added yet! Use /add_friend first')
        return
    
    success_count = 0
    failed_friends = []
    
    embed = discord.Embed(title="📨 Sending Messages to All Friends", color=discord.Color.gold())
    
    for friend_name, user_id in config['friends'].items():
        try:
            user = await bot.fetch_user(user_id)
            await user.send(message)
            success_count += 1
        except discord.NotFound:
            failed_friends.append(f"❌ {friend_name} - User ID not found")
        except discord.Forbidden:
            failed_friends.append(f"🔒 {friend_name} - DMs are DISABLED (ask them to enable DMs)")
        except Exception as e:
            failed_friends.append(f"⚠️ {friend_name} - Error: {str(e)}")
    
    embed.add_field(name="✅ Successfully Sent", value=f"{success_count}/{len(config['friends'])} friends", inline=False)
    if failed_friends:
        embed.add_field(name="Failed to Send", value="\n".join(failed_friends[:5]), inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="save_message", description="Save a message template for later use")
@app_commands.describe(
    message_name="Name for the template",
    message_text="The message to save"
)
async def save_message(interaction: discord.Interaction, message_name: str, message_text: str):
    config = load_friends_config()
    config['messages'][message_name] = message_text
    save_friends_config(config)
    await interaction.response.send_message(f'✅ Message "{message_name}" saved!')

@bot.tree.command(name="list_messages", description="List all saved messages")
async def list_messages(interaction: discord.Interaction):
    config = load_friends_config()
    if not config['messages']:
        await interaction.response.send_message('No messages saved yet!')
        return
    
    embed = discord.Embed(title="📝 Saved Messages", color=discord.Color.green())
    for name, text in config['messages'].items():
        embed.add_field(name=name, value=text, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="dm_with_template", description="Send a saved message template to a friend")
@app_commands.describe(
    friend_name="Friend's name",
    message_name="Template name"
)
async def dm_with_template(interaction: discord.Interaction, friend_name: str, message_name: str):
    config = load_friends_config()
    
    if message_name not in config['messages']:
        await interaction.response.send_message(f'❌ Message template "{message_name}" not found!')
        return
    
    if friend_name not in config['friends']:
        await interaction.response.send_message(f'❌ Friend "{friend_name}" not found!')
        return
    
    message = config['messages'][message_name]
    user_id = config['friends'][friend_name]
    
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        await interaction.response.send_message(f'✅ Message sent to {friend_name}!')
    except Exception as e:
        await interaction.response.send_message(f'❌ Error: {str(e)}')

@bot.tree.command(name="uppercase", description="Convert text to UPPERCASE")
@app_commands.describe(text="Text to convert")
async def uppercase(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(f"📤 {text.upper()}")

@bot.tree.command(name="lowercase", description="Convert text to lowercase")
@app_commands.describe(text="Text to convert")
async def lowercase(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(f"📥 {text.lower()}")

@bot.tree.command(name="reverse", description="Reverse text")
@app_commands.describe(text="Text to reverse")
async def reverse(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(f"🔄 {text[::-1]}")

@bot.tree.command(name="spam", description="Repeat text multiple times (max 10)")
@app_commands.describe(
    count="How many times to repeat (max 10)",
    text="Text to repeat"
)
async def spam(interaction: discord.Interaction, count: int, text: str):
    if count > 10:
        count = 10
    if count < 1:
        count = 1
    
    if len(text) > 100:
        await interaction.response.send_message("❌ Text is too long! Keep it under 100 characters")
        return
    
    total_length = len(text) * count
    if total_length > 1900:
        await interaction.response.send_message(f"❌ Message too long! ({total_length} chars) Max is 1900")
        return
    
    message = " ".join([text] * count)
    await interaction.response.send_message(message)

@bot.tree.command(name="echo", description="Echo text in the channel")
@app_commands.describe(text="Text to echo")
async def echo(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(text)

@bot.tree.command(name="embed", description="Send text as a nice embed")
@app_commands.describe(text="Text for the embed")
async def embed(interaction: discord.Interaction, text: str):
    embed_obj = discord.Embed(description=text, color=discord.Color.random())
    await interaction.response.send_message(embed=embed_obj)

@bot.tree.command(name="announce", description="Send an announcement embed")
@app_commands.describe(text="Announcement text")
async def announce(interaction: discord.Interaction, text: str):
    embed_msg = discord.Embed(title="📢 ANNOUNCEMENT", description=text, color=discord.Color.red())
    embed_msg.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed_msg)

@bot.tree.command(name="poll", description="Create a poll with reactions")
@app_commands.describe(
    question="Poll question",
    options="Options separated by commas (e.g., Red,Blue,Green)"
)
async def poll(interaction: discord.Interaction, question: str, options: str):
    option_list = [opt.strip() for opt in options.split(',')]
    
    if len(option_list) < 2:
        await interaction.response.send_message("❌ Need at least 2 options!")
        return
    
    if len(option_list) > 10:
        await interaction.response.send_message("❌ Maximum 10 options!")
        return
    
    embed_msg = discord.Embed(title="📊 POLL", description=question, color=discord.Color.purple())
    for i, option in enumerate(option_list, 1):
        embed_msg.add_field(name=f"Option {i}", value=option, inline=False)
    
    msg = await interaction.response.send_message(embed=embed_msg)
    
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    for i in range(len(option_list)):
        await msg.add_reaction(emojis[i])

@bot.tree.command(name="set_keyword", description="Set a keyword trigger for auto-response")
@app_commands.describe(
    keyword="The keyword to trigger on",
    response="Auto-response message"
)
async def set_keyword(interaction: discord.Interaction, keyword: str, response: str):
    config = load_friends_config()
    if 'keywords' not in config:
        config['keywords'] = {}
    
    config['keywords'][keyword.lower()] = response
    save_friends_config(config)
    await interaction.response.send_message(f'✅ Set keyword "{keyword}" → "{response}"')

@bot.tree.command(name="remove_keyword", description="Remove a keyword trigger")
@app_commands.describe(keyword="Keyword to remove")
async def remove_keyword(interaction: discord.Interaction, keyword: str):
    config = load_friends_config()
    if 'keywords' in config and keyword.lower() in config['keywords']:
        del config['keywords'][keyword.lower()]
        save_friends_config(config)
        await interaction.response.send_message(f'✅ Removed keyword "{keyword}"')
    else:
        await interaction.response.send_message(f'❌ Keyword "{keyword}" not found!')

@bot.tree.command(name="list_keywords", description="List all keyword triggers")
async def list_keywords(interaction: discord.Interaction):
    config = load_friends_config()
    if 'keywords' not in config or not config['keywords']:
        await interaction.response.send_message('No keywords set yet!')
        return
    
    embed_msg = discord.Embed(title="🔑 Keyword Triggers", color=discord.Color.green())
    for keyword, response in config['keywords'].items():
        embed_msg.add_field(name=keyword, value=response, inline=False)
    await interaction.response.send_message(embed=embed_msg)

@bot.tree.command(name="list_channels", description="List all channels in the server")
async def list_channels(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("❌ This command only works in servers!")
        return
    
    channels = guild.text_channels
    embed_msg = discord.Embed(title="📋 Server Channels", color=discord.Color.blue())
    
    channel_list = []
    for channel in channels:
        try:
            perms = channel.permissions_for(guild.me)
            if perms.send_messages:
                channel_list.append(f"✅ {channel.name} (ID: {channel.id})")
            else:
                channel_list.append(f"❌ {channel.name} (No access)")
        except:
            channel_list.append(f"❌ {channel.name} (Error checking)")
    
    for i in range(0, len(channel_list), 10):
        chunk = channel_list[i:i+10]
        if i == 0:
            embed_msg.add_field(name="Channels", value="\n".join(chunk), inline=False)
        else:
            embed_msg.add_field(name="More Channels", value="\n".join(chunk), inline=False)
    
    await interaction.response.send_message(embed=embed_msg)

@bot.tree.command(name="send_to_channel", description="Send a message to a specific channel")
@app_commands.describe(
    channel_id="Target channel ID",
    message="Message to send"
)
async def send_to_channel(interaction: discord.Interaction, channel_id: int, message: str):
    try:
        target_channel = bot.get_channel(channel_id)
        if not target_channel:
            await interaction.response.send_message(f"❌ Channel ID {channel_id} not found!\nMake sure bot is invited to that server.")
            return
        
        if target_channel.id == interaction.channel_id:
            await interaction.response.send_message("❌ Cannot send to the same channel! Use a different channel ID.")
            return
        
        perms = target_channel.permissions_for(target_channel.guild.me)
        if not perms.send_messages:
            await interaction.response.send_message(f"❌ Bot has NO permission to send messages in {target_channel.mention}")
            return
        
        await target_channel.send(message)
        embed_msg = discord.Embed(title="✅ Message Sent!", color=discord.Color.green())
        embed_msg.add_field(name="Channel", value=target_channel.mention, inline=False)
        embed_msg.add_field(name="Server", value=target_channel.guild.name, inline=False)
        await interaction.response.send_message(embed=embed_msg)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}")

@bot.tree.command(name="send_embed_to_channel", description="Send a formatted embed to a specific channel")
@app_commands.describe(
    channel_id="Target channel ID",
    message="Embed message"
)
async def send_embed_to_channel(interaction: discord.Interaction, channel_id: int, message: str):
    try:
        target_channel = bot.get_channel(channel_id)
        if not target_channel:
            await interaction.response.send_message(f"❌ Channel ID {channel_id} not found!")
            return
        
        if target_channel.id == interaction.channel_id:
            await interaction.response.send_message("❌ Cannot send to the same channel! Use a different channel ID.")
            return
        
        perms = target_channel.permissions_for(target_channel.guild.me)
        if not perms.send_messages:
            await interaction.response.send_message(f"❌ Bot has NO permission to send messages in {target_channel.mention}")
            return
        
        embed_msg = discord.Embed(description=message, color=discord.Color.random())
        embed_msg.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        embed_msg.set_footer(text=f"Sent via bot")
        await target_channel.send(embed=embed_msg)
        
        result = discord.Embed(title="✅ Embed Sent!", color=discord.Color.green())
        result.add_field(name="Channel", value=target_channel.mention, inline=False)
        result.add_field(name="Server", value=target_channel.guild.name, inline=False)
        await interaction.response.send_message(embed=result)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}")

@bot.tree.command(name="setup_prank", description="Setup which channel to prank")
@app_commands.describe(
    channel_id="Channel ID to prank (must be in a server bot can access)",
    server_name="Name of friend's server"
)
async def setup_prank(interaction: discord.Interaction, channel_id: int, server_name: str = "Friend's Server"):
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message(f"❌ Channel with ID {channel_id} not found! Make sure bot is invited to that server.")
            return
        
        perms = channel.permissions_for(channel.guild.me)
        if not perms.send_messages:
            await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}")
            return
        
        config = load_friends_config()
        config['prank_config']['friend_server_channel_id'] = channel_id
        config['prank_config']['friend_server_name'] = server_name
        save_friends_config(config)
        
        embed_msg = discord.Embed(title="✅ Prank Channel Set!", color=discord.Color.green())
        embed_msg.add_field(name="Channel", value=f"{channel.mention}", inline=False)
        embed_msg.add_field(name="Server", value=server_name, inline=False)
        embed_msg.add_field(name="Tip", value="Now use /prank or /prank_embed to send messages!", inline=False)
        await interaction.response.send_message(embed=embed_msg)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}")

@bot.tree.command(name="prank", description="Send a prank message to friend's server")
@app_commands.describe(message="Prank message")
async def prank(interaction: discord.Interaction, message: str):
    config = load_friends_config()
    channel_id = config.get('prank_config', {}).get('friend_server_channel_id', 0)
    
    if channel_id == 0:
        await interaction.response.send_message("❌ Prank channel not set! Use /setup_prank first!")
        return
    
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("❌ Prank channel not found! Use /setup_prank again.")
            return
        
        await channel.send(message)
        await interaction.response.send_message(f"😈 Prank sent to **{config['prank_config']['friend_server_name']}**! 🤣")
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}")

@bot.tree.command(name="prank_embed", description="Send a fancy prank embed to friend's server")
@app_commands.describe(message="Prank embed message")
async def prank_embed(interaction: discord.Interaction, message: str):
    config = load_friends_config()
    channel_id = config.get('prank_config', {}).get('friend_server_channel_id', 0)
    
    if channel_id == 0:
        await interaction.response.send_message("❌ Prank channel not set! Use /setup_prank first!")
        return
    
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("❌ Prank channel not found! Use /setup_prank again.")
            return
        
        embed_msg = discord.Embed(description=message, color=discord.Color.red())
        embed_msg.set_footer(text="This is a prank! 😜")
        await channel.send(embed=embed_msg)
        await interaction.response.send_message(f"😈 Prank embed sent to **{config['prank_config']['friend_server_name']}**! 🤣")
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}")

@bot.tree.command(name="prank_status", description="Check if prank channel is configured")
async def prank_status(interaction: discord.Interaction):
    config = load_friends_config()
    channel_id = config.get('prank_config', {}).get('friend_server_channel_id', 0)
    server_name = config.get('prank_config', {}).get('friend_server_name', '')
    
    if channel_id == 0 or not server_name:
        await interaction.response.send_message("❌ Prank channel not set! Use /setup_prank first!")
        return
    
    embed_msg = discord.Embed(title="😈 Prank Status", color=discord.Color.orange())
    embed_msg.add_field(name="Server", value=server_name, inline=False)
    embed_msg.add_field(name="Channel ID", value=channel_id, inline=False)
    embed_msg.add_field(name="Ready to Prank?", value="✅ YES! Use /prank or /prank_embed", inline=False)
    await interaction.response.send_message(embed=embed_msg)

@bot.tree.command(name="info", description="Show server and user info")
async def info(interaction: discord.Interaction):
    guild = interaction.guild
    embed_msg = discord.Embed(title="ℹ️ Server Info", color=discord.Color.blue())
    embed_msg.add_field(name="Server Name", value=guild.name, inline=False)
    embed_msg.add_field(name="Members", value=guild.member_count, inline=False)
    embed_msg.add_field(name="Created", value=guild.created_at.strftime('%Y-%m-%d'), inline=False)
    embed_msg.add_field(name="You", value=interaction.user.name, inline=False)
    embed_msg.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await interaction.response.send_message(embed=embed_msg)

@bot.tree.command(name="avatar", description="Show user avatar")
@app_commands.describe(user="User to show avatar for (default: yourself)")
async def avatar(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user
    embed_msg = discord.Embed(title=f"{user.name}'s Avatar", color=discord.Color.blurple())
    embed_msg.set_image(url=user.avatar.url if user.avatar else None)
    await interaction.response.send_message(embed=embed_msg)

@bot.tree.command(name="clear", description="Delete recent messages (mod only)")
@app_commands.describe(amount="Number of messages to delete (max 100)")
async def clear(interaction: discord.Interaction, amount: int = 10):
    if amount > 100:
        amount = 100
    
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You need manage messages permission!", ephemeral=True)
        return
    
    try:
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"✅ Deleted {len(deleted)} messages!", ephemeral=True, delete_after=5)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="broadcast", description="Send a message to ALL channels (admin only)")
@app_commands.describe(message="Message to broadcast")
async def broadcast(interaction: discord.Interaction, message: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permission!", ephemeral=True)
        return
    
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("❌ This command only works in servers!", ephemeral=True)
        return
    
    channels = guild.text_channels
    success = 0
    failed = 0
    
    await interaction.response.defer()
    
    for channel in channels:
        try:
            perms = channel.permissions_for(guild.me)
            if perms.send_messages:
                await channel.send(message)
                success += 1
            else:
                failed += 1
        except:
            failed += 1
    
    embed_msg = discord.Embed(title="📢 Broadcast Complete", color=discord.Color.green())
    embed_msg.add_field(name="✅ Sent To", value=f"{success} channels", inline=True)
    embed_msg.add_field(name="❌ Failed", value=f"{failed} channels", inline=True)
    await interaction.followup.send(embed=embed_msg)

@bot.tree.command(name="join", description="Join your voice channel")
async def join(interaction: discord.Interaction):
    """Join the voice channel of the user who ran the command"""
    if not interaction.user.voice:
        await interaction.response.send_message("❌ You must be in a voice channel!")
        return
    
    channel = interaction.user.voice.channel
    
    try:
        # Check if already in same channel
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.channel == channel:
                await interaction.response.send_message(f"✅ Bot is already in **{channel.name}**!")
                return
            # Disconnect from other channel
            try:
                await interaction.guild.voice_client.disconnect(force=True)
            except:
                pass
            
            import asyncio
            await asyncio.sleep(1)
        
        # Connect to voice channel
        vc = await channel.connect()
        
        # Track this channel so bot auto-rejoins if kicked
        voice_channels_to_keep[interaction.guild.id] = channel.id
        
        embed_msg = discord.Embed(title="🔊 Bot Joined!", color=discord.Color.green())
        embed_msg.add_field(name="Channel", value=channel.name, inline=False)
        embed_msg.add_field(name="Status", value="Bot will stay in VC and auto-rejoin if disconnected!", inline=False)
        await interaction.response.send_message(embed=embed_msg)
            
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}")

@bot.tree.command(name="leave", description="Leave the voice channel")
async def leave(interaction: discord.Interaction):
    """Leave the current voice channel"""
    if not interaction.guild.voice_client:
        await interaction.response.send_message("❌ Bot is not in a voice channel!")
        return
    
    try:
        channel_name = interaction.guild.voice_client.channel.name
        # Stop auto-rejoining
        if interaction.guild.id in voice_channels_to_keep:
            del voice_channels_to_keep[interaction.guild.id]
        
        await interaction.guild.voice_client.disconnect(force=True)
        await interaction.response.send_message(f"✅ Bot left **{channel_name}**!")
    except Exception as e:
        print(f"Error leaving VC: {e}")
        await interaction.response.send_message(f"❌ Error: {str(e)}")

@bot.tree.command(name="help", description="Show all available commands")
async def help_bot(interaction: discord.Interaction):
    embed_msg = discord.Embed(title="🤖 Bot Help - All Commands", color=discord.Color.blurple())
    
    embed_msg.add_field(name="😈 Prank Commands", value="`/setup_prank` `/prank` `/prank_embed` `/prank_status`", inline=False)
    embed_msg.add_field(name="📬 Friend Commands", value="`/add_friend` `/remove_friend` `/list_friends` `/dm_friend` `/dm_all`", inline=False)
    embed_msg.add_field(name="💬 Message Templates", value="`/save_message` `/list_messages` `/dm_with_template`", inline=False)
    embed_msg.add_field(name="✏️ Text Features", value="`/uppercase` `/lowercase` `/reverse` `/spam` `/echo` `/embed`", inline=False)
    embed_msg.add_field(name="📨 Channel Commands", value="`/list_channels` `/send_to_channel` `/send_embed_to_channel`", inline=False)
    embed_msg.add_field(name="🔑 Keyword Triggers", value="`/set_keyword` `/remove_keyword` `/list_keywords`", inline=False)
    embed_msg.add_field(name="📢 Other Commands", value="`/announce` `/poll` `/info` `/avatar` `/broadcast` `/clear`", inline=False)
    embed_msg.add_field(name="🔊 Voice Commands", value="`/join` `/leave`", inline=False)
    embed_msg.add_field(name="💡 Pro Tips", value="Use `/prank` and `/prank_embed` for best pranks! Keyword triggers work in any message!", inline=False)
    
    embed_msg.set_footer(text="All commands are slash commands (/) now!")
    
    await interaction.response.send_message(embed=embed_msg)

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not set! Please create a .env file with your bot token.")
        print("See .env.example for the format.")
    else:
        bot.run(DISCORD_TOKEN)
