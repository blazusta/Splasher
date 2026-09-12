import discord, random, asyncio, json
from discord.ext import commands
from datetime import timezone, datetime
from pathlib import Path

class Config(commands.Cog):

    server_data = Path(__file__).resolve().parent.parent / "data" / "discord_server_data.json"

    def __init__(self, bot):
        self.bot = bot

        with open(Config.server_data, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.member_join_channel_id = data["member_join_channel_id"]
            self.join_role_id = data["join_role_id"]


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Successfully initiated. {self.bot.user.name} is ready to receive commands.")


    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        
        # to make sure the event is logged into the audit log
        # otherwise the event could be trigged before even it's logged
        # which can display a leaving message for a banned/kicked member
        await asyncio.sleep(0.5)
        channel = self.bot.get_channel(self.member_join_channel_id)

        if channel:
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
        channel = self.bot.get_channel(self.member_join_channel_id)

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
        
        try:
            default_role = discord.utils.get(member.guild.roles, id=self.join_role_id)
            if default_role:
                await member.add_roles(default_role)
        except discord.Forbidden:
            # If the bot isn't authorized to access server roles
            # catch the error and pass
            pass

        if channel:
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
    async def set_welcome(self, ctx, channel: discord.TextChannel):
        if ctx.author.guild_permissions.administrator:
            with open(Config.server_data, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data["member_join_channel_id"] = channel.id

            with open(Config.server_data, 'w') as f:
                json.dump(data ,f, indent=4)
                self.member_join_channel_id = channel.id
                await ctx.reply(f"Successfully set welcoming channel to {channel.mention}")
        else:
            await ctx.reply("You do not have permission to do that.")


    @set_welcome.error
    async def set_welcome_error(self, ctx, error):

        # in case the user types a non-existant channel
        if isinstance(error, commands.ChannelNotFound):
            await ctx.reply("Couldn't find this channel.")

        # in case the user doesn't specify a channel (missing argument)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("Please specify a channel.")
            

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.add_cog(Config(self))