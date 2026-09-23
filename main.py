from dotenv import load_dotenv
from discord.ext import commands
import os, discord, aiohttp, asyncio, traceback

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# Start with standard permissions (server updates, role updates, etc.)
intents = discord.Intents.default()

intents.members = True
intents.message_content = True

# We inherit from commands.Bot so we can customize startup behavior cleanly
class MyBot(commands.Bot):

    # setup_hook runs automatically ONCE before the bot connects to Discord
    async def setup_hook(self):
        # Load external feature files (Cogs) dynamically
        await self.load_extension("cogs.onboarding")
        await self.load_extension("cogs.chat_moderation")
        await self.load_extension("cogs.member_moderation")
        await self.load_extension("cogs.anti_spam")
        
        # Send and register all slash commands (/) to Discord servers
        await self.tree.sync()
        print("Slash commands synced successfully.")

bot = MyBot(command_prefix='!', intents=intents)

async def start_bot():
    # 'async with bot' is an asynchronous context manager.
    # It automatically opens and cleans up network sessions (prevents memory leaks and crashes)
    async with bot:
        try:
            try:
                # Login and connect the bot to Discord using the secret token
                await bot.start(BOT_TOKEN)

            # Handle network drops, timeouts, or Discord connection failures gracefully
            except (aiohttp.ClientError, asyncio.TimeoutError, discord.GatewayNotFound) as e:
                print(f"Connection Failed: {e}")

            except Exception:
                print(f"Unexpected Error occurred:")
                # Print the full error path and exact line number to help fix it
                traceback.print_exc()

        # Catch manual shutdown (Ctrl + C) inside the async task
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    # Start Python's async event loop and run the start_bot function
    try: asyncio.run(start_bot())  
    except KeyboardInterrupt: print("Bot shut down by user.")