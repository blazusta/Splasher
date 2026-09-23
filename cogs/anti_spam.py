import discord
import asyncio
from discord.ext import commands
from datetime import timedelta
from time import time

class AntiSpam(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.user_messages = {}
        self.recently_punished = set()

        
    @commands.Cog.listener()
    async def on_message(
        self, 
        message: discord.Message
    ):
        
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Ignore DMs (private messages)
        if message.guild is None:
            return
        
        # If a member is authorized, ignore
        if message.author.guild_permissions.manage_messages or message.author.guild_permissions.administrator:
            return
        
        user_id = message.author.id

        # delete message sent while waiting for discord servers to timeout the spammer
        if user_id in self.recently_punished:
            try:
                await message.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass
            return
        
        current_time = time()

        # If user sends a message for the first time, add them to the dict
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []

        # append user's message time
        self.user_messages[user_id].append(current_time)

        # generate a new list each time the user sends a message
        # why: to keep track of the messages sent in the last 5 seconds only
        self.user_messages[user_id] = [t for t in self.user_messages[user_id] if current_time - t < 5]

        # check if user has sent more than 5 messages in 5 seconds
        if len(self.user_messages[user_id]) > 5:
            self.user_messages[user_id] = []

            # check role hierarchy
            if message.author.top_role >= message.guild.me.top_role:
                return
            
            self.recently_punished.add(user_id)
            
            try:
                await message.author.timeout(
                    timedelta(minutes=15),
                    reason="Spam Triggered"
                )

                await asyncio.sleep(0.5)
                
                try:
                    await message.channel.purge(
                        limit=20,
                        # m is a parameter (purge func passes discord.Message object to m)
                        check= lambda m: m.author.id == user_id
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

                await message.channel.send(
                    f"{message.author.mention} has been timed out for 15 minutes due to spamming.",
                    delete_after=5
                )

                try:
                    await message.author.send(
                        f"You have been timed out in {message.guild.name} for 15 minutes.\n**Reason:** Spam Triggered"
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

            except (discord.Forbidden, discord.HTTPException):
                pass

            finally:
                await asyncio.sleep(2)
                self.recently_punished.discard(user_id) 


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiSpam(bot))