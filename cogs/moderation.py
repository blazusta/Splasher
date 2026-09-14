import discord
from discord import app_commands
from discord.ext import commands

class ModConfig(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command(name="clear", description="Clear a specified number of messages in this channel")
    @app_commands.describe(amount="The number of messages to delete (between 1 and 100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear_messages(self, interaction: discord.Interaction, amount: int):
        
        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                "Amount should be ranged between 1 and 100.",
                ephemeral=True  # Only you can see this message
            )
            return
        
        # - Bot is thinking... (seen ephemerally by user)
        # - Basically tells discord to grant the bot more time to execute the command
        # - If this line wasn't implemented, discord would've been aborted the command
        #   if the process exceeded 3 seconds.
        await interaction.response.defer(ephemeral=True)

        try:
            await interaction.channel.purge(limit=amount)
            reply = f"Successfully deleted {amount} message" if amount == 1 else f"Successfully deleted {amount} messages"
            await interaction.followup.send(
                reply,
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "I do not have permission to delete messages in this channel",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                f"Failed to delete messages: {e}",
                ephemeral=True
            )


    @clear_messages.error
    async def clear_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You need the `Manage Messages` permission to use this command.",
                ephemeral=True
            )


    @app_commands.command(name="purge", description="Purge all messages sent in the last 14 days.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge_messaged(self, interaction: discord.Interaction):
        
        await interaction.response.defer(ephemeral=True)

        try:
            # limit=None (delete all)
            # channel.purge returns a list of message objects that were deleted
            deleted = await interaction.channel.purge(limit=None)

            # if delete is an empty list
            if not deleted:
                await interaction.followup.send(
                    f"{interaction.channel.mention} is empty or has no messages sent in the last 14 days.",
                    ephemeral=True
                )
                return

            reply = f"Successfully purged {interaction.channel.mention}"
            followup_reply = "\n1 message has been deleted." if len(deleted) == 0 else f"\n{len(deleted)} messages have been deleted."
            await interaction.followup.send(
                f"{reply}{followup_reply}",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "I do not have permission to delete messages in this channel",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                f"Failed to delete messages: {e}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(ModConfig(bot))