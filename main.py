from dotenv import load_dotenv
from cogs import onboarding
import os, discord, aiohttp, asyncio

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = onboarding.MyBot(command_prefix='!', intents=intents)

async def start_bot():
    try:
        while True:
            try:
                await bot.start(BOT_TOKEN)

            except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
                print(f"Connection Failed: {e}\nRetrying...")
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"Unexpected Error occurred: {e}")
                break

    except KeyboardInterrupt:
        pass

    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("Interrupted by user.")