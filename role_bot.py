import discord
from discord.ext import commands
import asyncio

TOKEN = 'lol nice try'

# Set up intents (required for accessing member data)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def assign_role(ctx, user_id: int, role_id: int):
    """Assigns a role to a specific user by their ID."""
    guild = ctx.guild
    member = guild.get_member(user_id)
    role = guild.get_role(role_id)
    
    if not member:
        await ctx.send("User not found in this server.")
        return
    
    if not role:
        await ctx.send("Role not found.")
        return
    
    try:
        if role not in member.roles:
            await member.add_roles(role)
            await ctx.send(f"Assigned **{role.name}** to **{member.display_name}**")
        else:
            await ctx.send(f"**{member.display_name}** already has the **{role.name}** role.")
    except discord.errors.Forbidden:
        await ctx.send(f"Insufficient permissions to assign **{role.name}** to **{member.display_name}**")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
async def assign_role_bulk(ctx, role_id: int, *user_ids: int):
    """Assigns a role to multiple users at once. Usage: !assign_role_bulk <role_id> <user_id1> <user_id2> ..."""
    if not user_ids:
        await ctx.send("Please provide at least one user ID.")
        return
    
    guild = ctx.guild
    role = guild.get_role(role_id)
    
    if not role:
        await ctx.send("Role not found.")
        return
    
    # Send initial status message
    status_msg = await ctx.send(f"Processing {len(user_ids)} users...")
    
    success_count = 0
    already_have = 0
    not_found = 0
    errors = 0
    
    for i, user_id in enumerate(user_ids):
        member = guild.get_member(user_id)
        
        if not member:
            not_found += 1
            continue
        
        if role in member.roles:
            already_have += 1
            continue
        
        try:
            await member.add_roles(role)
            success_count += 1
            
            # Update status every 10 users or on last user
            if (i + 1) % 10 == 0 or i == len(user_ids) - 1:
                await status_msg.edit(content=f"Processed {i + 1}/{len(user_ids)} users...")
            
            # Rate limiting: small delay between role assignments
            await asyncio.sleep(0.5)
            
        except discord.errors.Forbidden:
            errors += 1
        except Exception:
            errors += 1
    
    # Final status report
    result_msg = f"**Bulk Role Assignment Complete**\n"
    result_msg += f"**Role:** {role.name}\n"
    result_msg += f"**Successfully assigned:** {success_count}\n"
    result_msg += f"**Already had role:** {already_have}\n"
    result_msg += f"**Users not found:** {not_found}\n"
    result_msg += f"**Errors:** {errors}\n"
    result_msg += f"**Total processed:** {len(user_ids)}"
    
    await status_msg.edit(content=result_msg)

@bot.command()
async def remove_role(ctx, user_id: int, role_id: int):
    """Removes a role from a specific user."""
    guild = ctx.guild
    member = guild.get_member(user_id)
    role = guild.get_role(role_id)
    
    if not member:
        await ctx.send("User not found in this server.")
        return
    
    if not role:
        await ctx.send("Role not found.")
        return
    
    try:
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"Removed **{role.name}** from **{member.display_name}**")
        else:
            await ctx.send(f"**{member.display_name}** doesn't have the **{role.name}** role.")
    except discord.errors.Forbidden:
        await ctx.send(f"Insufficient permissions to remove **{role.name}** from **{member.display_name}**")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
async def get_role_id(ctx, *, role_name):
    """Gets the ID of a role by its name."""
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=role_name)
    
    if role:
        await ctx.send(f"**{role.name}** ID: `{role.id}`")
    else:
        await ctx.send(f"Role '{role_name}' not found.")

@bot.command()
async def get_user_id(ctx, *, user_mention_or_name):
    """Gets user ID from mention or username."""
    try:
        # Try to get user from mention
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
            await ctx.send(f"**{user.display_name}** ID: `{user.id}`")
        else:
            # Try to find by name
            member = discord.utils.get(ctx.guild.members, display_name=user_mention_or_name)
            if not member:
                member = discord.utils.get(ctx.guild.members, name=user_mention_or_name)
            
            if member:
                await ctx.send(f"**{member.display_name}** ID: `{member.id}`")
            else:
                await ctx.send(f"User '{user_mention_or_name}' not found.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
async def assign_from_reaction(ctx, message_id: int, emoji: str, role_id: int):
    """Assigns a role to all users who reacted with a specific emoji to a message."""
    try:
        # Get the message - search across all channels in the guild
        message = None
        for channel in ctx.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
                break
            except (discord.NotFound, discord.Forbidden):
                continue
        
        if not message:
            await ctx.send("Message not found in any accessible channel.")
            return
        
        # Find the reaction
        target_reaction = None
        for reaction in message.reactions:
            if str(reaction.emoji) == emoji:
                target_reaction = reaction
                break
        
        if not target_reaction:
            await ctx.send(f"No reactions found with emoji {emoji}")
            return
        
        # Get the role
        role = ctx.guild.get_role(role_id)
        if not role:
            await ctx.send("Role not found.")
            return
        
        # Get users who reacted
        users = []
        async for user in target_reaction.users():
            if not user.bot:  # Skip bots
                users.append(user)
        
        if not users:
            await ctx.send(f"No users found who reacted with {emoji}")
            return
        
        # Send initial status
        status_msg = await ctx.send(f"Processing {len(users)} users who reacted with {emoji}...")
        
        success_count = 0
        already_have = 0
        errors = 0
        
        for i, user in enumerate(users):
            member = ctx.guild.get_member(user.id)
            
            if not member:
                continue
            
            if role in member.roles:
                already_have += 1
                continue
            
            try:
                await member.add_roles(role)
                success_count += 1
                
                # Update status every 10 users
                if (i + 1) % 10 == 0 or i == len(users) - 1:
                    await status_msg.edit(content=f"Processed {i + 1}/{len(users)} users...")
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except discord.errors.Forbidden:
                errors += 1
            except Exception:
                errors += 1
        
        # Final status report
        result_msg = f"**Role Assignment from Reactions Complete**\n"
        result_msg += f"**Role:** {role.name}\n"
        result_msg += f"**Emoji:** {emoji}\n"
        result_msg += f"**Successfully assigned:** {success_count}\n"
        result_msg += f"**Already had role:** {already_have}\n"
        result_msg += f"**Errors:** {errors}\n"
        result_msg += f"**Total processed:** {len(users)}"
        
        await status_msg.edit(content=result_msg)
        
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
async def help_roles(ctx):
    """Shows available role management commands."""
    help_text = """
**Bot commands:**

**Basic Commands:**
`!assign_role <user_id> <role_id>` - Assign role to one user
`!remove_role <user_id> <role_id>` - Remove role from one user

**Bulk Commands:**
`!assign_role_bulk <role_id> <user_id1> <user_id2> ...` - Assign role to multiple users
`!assign_from_reaction <message_id> <emoji> <role_id>` - Assign role to users who reacted

**Utility Commands:**
`!get_role_id <role_name>` - Get role ID by name
`!get_user_id <@user or username>` - Get user ID
`!help_roles` - Show this help message

You need "Manage Roles" permission to use role assignment commands.
    """
    await ctx.send(help_text)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required arguments. Use `!help_roles` for command usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument provided. Make sure user/role IDs are numbers.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    else:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    bot.run(TOKEN)
