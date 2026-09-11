import discord, random, json
from discord.ext import commands
from pathlib import Path

class Welcome(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

        # __file__ : attribute that contains the name of the file 'welcome.py'
        # Path(__file__): turns the text 'welcome.py' into an object
        # .resolve(): turns the path into an Absolute path
        # .parent: go back by one folder
        # '/' used for path joining
        DISCORD_SERVER_DATA = Path(__file__).resolve().parent.parent / "data" / "discord_server_data.json"

        with open(file=DISCORD_SERVER_DATA, mode='r', encoding='utf-8') as file:
            server_data = json.load(file)
            self.member_join_channel_id = server_data["member_join_channel_id"]

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Successfully initiated. {self.bot.user.name} is ready to receive commands.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel_id = self.member_join_channel_id
        channel = self.bot.get_channel(channel_id)

        if channel:
            welcomings = [
                f"Have the waves led you here? {member.mention}", 
                f"{member.mention} has made it to the server 🌊",
                f"Glad to have you here! {member.mention}",
                f"{member.mention} has joined the party 🔥",
                f"{member.mention} stumbled upon greatness..."
            ]

            random_welcoming = random.choice(welcomings)
            await channel.send(random_welcoming)
            

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.add_cog(Welcome(self))