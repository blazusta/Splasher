from dotenv import load_dotenv
from cogs import onboarding
import os, discord

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = onboarding.MyBot(command_prefix='!', intents=intents)
bot.run(BOT_TOKEN)