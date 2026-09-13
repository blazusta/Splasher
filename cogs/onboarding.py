import discord, random, asyncio, json
from discord.ext import commands
from datetime import timezone, datetime
from pathlib import Path

class Config(commands.Cog):

    server_data = Path(__file__).resolve().parent.parent / "data" / "discord_server_data.json"

    def __init__(self, bot):
        self.bot = bot

        with open(Config.server_data, 'r', encoding='utf-8') as f:
            self.server_config = json.load(f)


                            # [Config class events and commands]


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Successfully initiated. {self.bot.user.name} is ready to receive commands.")


    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):

        guild_id = str(member.guild.id)
        guild_config = self.server_config.get(guild_id, {})

        channel_id = guild_config.get("member_join_channel_id")
        if not channel_id:
            # if the channel_id was not found in the json file, return.
            return
        
        channel = self.bot.get_channel(channel_id)
        if not channel:
            # if the channel is None (non-existent), return
            return
        
        # to make sure the event is logged into the audit log
        # otherwise the event could be trigged before even it's logged
        # which can display a leaving message for a banned/kicked member
        await asyncio.sleep(0.5)
    
        was_kicked_or_banned = False
        current_time = datetime.now(timezone.utc)

        # async loop that checks in the audit log whether the left member was banned or not
        # timedelta is to confirm that the banned user was banned just now
        # we check if the ban happened at the same time of the left member

        # seconds < 5: because it takes time for the discord bot to retreive event data
        # and notify the bot through the websocket.
        try:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.ban):
                timedelta = current_time - entry.created_at
                seconds = timedelta.total_seconds()

                if member.id == entry.target.id and seconds < 5:
                    was_kicked_or_banned = True
                    break
                
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.kick):
                timedelta = current_time - entry.created_at
                seconds = timedelta.total_seconds()

                if member.id == entry.target.id and seconds < 5:
                    was_kicked_or_banned = True
                    break
        except discord.Forbidden:
            # If the bot isn't authorized to access audit logs
            # catch the error and pass
            pass


        if not was_kicked_or_banned:
            farewell = [
                f"Why did you leave us? {member.name}",
                f"{member.name} has unfortunately left the server."
            ]

            random_farewell = random.choice(farewell)
                
            embed = discord.Embed(
                title=f"Leaving {member.guild.name.upper()}",
                description=random_farewell,
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(
                name="Remaining Members", 
                value=f"#{member.guild.member_count}", 
                inline=True
            )
            embed.set_footer(
                text=f"User ID: {member.id}",
                icon_url=member.guild.icon.url if member.guild.icon else None,
            )

            await channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        guild_id = str(member.guild.id)
        guild_config = self.server_config.get(guild_id, {})

        channel_id = guild_config.get("member_join_channel_id")
        if not channel_id:
            return
        
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        # bots don't need welcoming, do they?
        if member.bot:
            return

        try:
            await member.send(f"Welcome to {member.guild.name.upper()} {member.mention}")
        except discord.Forbidden:
            # If the user does not allow DMs, pass (403 forbidden)
            pass
        except discord.HTTPException:
            # If the user does not allow DMs, pass (400 bad request)
            pass
        
        guild_default_role = guild_config.get("join_role_id")
        if guild_default_role:
            try:
                default_role = discord.utils.get(member.guild.roles, id=guild_default_role)
                if default_role:
                    await member.add_roles(default_role)
            except discord.Forbidden:
                # If the bot isn't authorized to access server roles
                # catch the error and pass
                pass
        welcomings = [
            f"Have the waves led you here? {member.mention}", 
            f"{member.mention} has made it to the server 🌊",
            f"Glad to have you here! {member.mention}",
            f"{member.mention} has joined the party 🔥",
            f"{member.mention} stumbled upon greatness..."
        ]
        random_welcoming = random.choice(welcomings)
            
        embed = discord.Embed(
            title=f"Welcome to {member.guild.name.upper()}",
            description=random_welcoming,
            color=0x00A8FF,
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="Account Created", 
            value=member.created_at.strftime("%Y / %m / %d"), 
            inline=True
        )
        embed.add_field(
            name="Member Count", 
            value=f"#{member.guild.member_count}", 
            inline=True
        )
        embed.set_footer(
            text=f"User ID: {member.id}",
            icon_url=member.guild.icon.url if member.guild.icon else None,
        )

        await channel.send(embed=embed)


    @commands.command(name="set_welcome")
    @commands.guild_only()
    async def set_welcome(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        if ctx.author.guild_permissions.administrator:
            with open(Config.server_data, 'r', encoding='utf-8') as f:
                server_config = json.load(f)

            if guild_id not in server_config:
                server_config[guild_id] = {
                "member_join_channel_id": None,
                "join_role_id": None
            }
                    
            server_config[guild_id]["member_join_channel_id"] = channel.id

            with open(Config.server_data, 'w', encoding='utf-8') as f:
                json.dump(server_config ,f, indent=4)

            self.server_config = server_config
            await ctx.reply(f"Successfully set welcoming channel to {channel.mention}")
        else:
            await ctx.reply("You do not have permission to do that.")


    @commands.command(name="set_role")
    @commands.guild_only()
    async def set_role(self, ctx, role: discord.Role):
        if ctx.author.guild_permissions.administrator:
            # Is the role the admin wants to assign to member higher than bot role?
            if role >= ctx.guild.me.top_role:
                await ctx.reply(f"I cannot assign {role.mention} because it is higher than or equal to my highest role in the server hierarchy.")
                return
            
            # Is the role the admin wants to assign to member a default role? (everyone, here)
            # Is the role the admin wants to assign a bot-managed role? (Splasher)
            if role.is_default() or role.managed:
                await ctx.reply(f"You cannot set `@everyone | @here` or bot-managed roles as a default join role.")
                return
            
            
            guild_id = str(ctx.guild.id)
            
            with open(Config.server_data, 'r', encoding='utf-8') as f:
                server_config = json.load(f)

            if guild_id not in server_config:
                server_config[guild_id] = {
                    "member_join_channel_id": None,
                    "join_role_id": None
                }

            server_config[guild_id]["join_role_id"] = role.id

            with open(Config.server_data, 'w', encoding='utf-8') as f:
                json.dump(server_config, f, indent=4)

            self.server_config = server_config
            await ctx.reply(f"Successfully set default join role to {role.mention}")
        else:
            await ctx.reply(f"You do not have permission to do that.")


                        # [Handle event/command errors and exceptions]


    @set_welcome.error
    async def set_welcome_error(self, ctx, error):

        # in case the user types a non-existant channel
        if isinstance(error, commands.ChannelNotFound):
            await ctx.reply("Couldn't find this channel.")

        # in case the user doesn't specify a channel (missing argument)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("Please specify a channel.")

        # in case the user types the command in the bot's DM
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.reply("This command can only be used within servers.")
            

    @set_role.error
    async def set_role_error(self, ctx, error):

        if isinstance(error, commands.RoleNotFound):
            arg = str(error.argument)
            # discord.Role in python either receives <@ or <@&
            # Discord passes an argument that starts with <@ if it catches a member mention
            # and passes an argument that starts with <@& if it catches a role mention
            # discord.py handles the decoding, and it converts the argument based on
            # what it starts with
            if arg.startswith('<@') and not arg.startswith('<@&'):
                await ctx.reply(f"This is not a role 🤦‍♂️")
            else:
                await ctx.reply("Couldn't find this role.")

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("Please specify a role.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.reply("This command can only be used within servers.")


class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.add_cog(Config(self))