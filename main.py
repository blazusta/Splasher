from dotenv import load_dotenv
from discord.ext import commands
import os, discord, aiohttp, asyncio, traceback

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("cogs.onboarding")
        await self.load_extension("cogs.chat_moderation")
        await self.load_extension("cogs.member_moderation")
        
        await self.tree.sync()
        print("Slash commands synced successfully.")

bot = MyBot(command_prefix='!', intents=intents)

async def start_bot():
    async with bot:
        try:
            try:
                await bot.start(BOT_TOKEN)

            except (aiohttp.ClientError, asyncio.TimeoutError, discord.GatewayNotFound) as e:
                print(f"Connection Failed: {e}")

            except Exception:
                print(f"Unexpected Error occurred:")
                traceback.print_exc()

        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    try: asyncio.run(start_bot())  
    except KeyboardInterrupt: print("Bot shut down by user.")