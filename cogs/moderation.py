import discord
from discord import app_commands
from discord.ext import commands

class ModConfig(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.guild_only()
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
            deleted = await interaction.channel.purge(limit=amount)

            if not deleted:
                await interaction.followup.send(
                    f"{interaction.channel.mention} is empty or has no messages sent in the last 14 days.",
                    ephemeral=True
                )
                return
            
            reply = f"Successfully deleted 1 message" if len(deleted) == 1 else f"Successfully deleted {len(deleted)} messages"
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


    @app_commands.guild_only()
    @app_commands.command(name="purge", description="Purge all messages sent in the last 14 days.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge_messages(self, interaction: discord.Interaction):
        
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

            reply = f"{interaction.channel.mention} has been cleared 🌊"
            followup_reply = "\n1 message has been deleted." if len(deleted) == 1 else f"\n{len(deleted)} messages have been deleted."
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

    @purge_messages.error
    async def purge_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You need the `Manage Messages` permission to use this command.",
                ephemeral=True
            )


    @app_commands.guild_only()
    @app_commands.command(name="slowmode", description="Cooldown timer to prevent spam")
    @app_commands.describe(time="Specify time in seconds")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(
        self, 
        interaction: discord.Interaction, 
        time: app_commands.Range[int, 0, 21600] # 0 to 6h
    ):
        try:
            await interaction.channel.edit(slowmode_delay=time)

            if time == 0:
                await interaction.response.send_message(
                    f"Slowmode has been disabled for {interaction.channel.mention}",
                    ephemeral=True  
                )
                return
            
            await interaction.response.send_message(
                f"Slowmode has been set for {interaction.channel.mention}: {time}s",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have permission to slowmode this channel",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Failed to slowmode channel: {e}",
                ephemeral=True
            )

    @slowmode.error
    async def slowmode_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You need the `Manage Channels` permission to use this command.",
                ephemeral=True
            )


    @app_commands.guild_only()
    @app_commands.command(name="lock", description="Prevent @everyone from sending messages in this channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock_channel(self, interaction: discord.Interaction):

        everyone = interaction.channel.permissions_for(interaction.guild.default_role)
        if everyone.send_messages:
            try:
                await interaction.channel.set_permissions(
                    interaction.guild.default_role, # @everyone
                    send_messages=False
                )
                await interaction.response.send_message(
                    f"{interaction.channel.mention} has been locked 🔒",
                    ephemeral=True
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I do not have the permission to manage permissions for this channel.",
                    ephemeral=True
                )
            except discord.HTTPException as e:
                await interaction.response.send_message(
                    f"Failed to lock channel: {e}",
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                f"{interaction.channel.mention} is already locked!",
                ephemeral=True
            )

    @lock_channel.error
    async def lock_channel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You need the `Manage Channels` permission to use this command.",
                ephemeral=True
            )


    @app_commands.guild_only()
    @app_commands.command(name="unlock", description="Allow @everyone to send messages in this channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock_channel(self, interaction: discord.Interaction):
        
        everyone = interaction.channel.permissions_for(interaction.guild.default_role)
        if not everyone.send_messages:
            try:
                await interaction.channel.set_permissions(
                    interaction.guild.default_role,
                    send_messages=None  # reset this permission to server default value (T/F)
                )
                await interaction.response.send_message(
                    f"{interaction.channel.mention} has been unlocked 🔓",
                    ephemeral=True
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I do not have the permission to manage permissions for this channel.",
                    ephemeral=True
                )
            except discord.HTTPException as e:
                await interaction.response.send_message(
                    f"Failed to unlock channel: {e}",
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                f"{interaction.channel.mention} is already unlocked!",
                ephemeral=True
            )

    @unlock_channel.error
    async def unlock_channel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You need the `Manage Channels` permission to use this command.",
                ephemeral=True
            )


    @app_commands.guild_only()
    @app_commands.command(name="kick", description="Kick a member from your server")
    @app_commands.describe(member="The member to kick", reason="Reason for kicking")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_member(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member,
        reason: str = "No reason provided." # default reason output if it wasn't specified
    ):
        
        # Command trigger cannot kick themselves
        if member == interaction.user:
            await interaction.response.send_message(
                "You cannot kick yourself 🤨",
                ephemeral=True
            )
            return
        
        # Server owner cannot be kicked by who has `kick member` permission
        if member == interaction.guild.owner:
            await interaction.response.send_message(
                "You cannot kick the server owner 😠",
                ephemeral=True
            )
            return 
        
        # A mod cannot kick an admin/owner
        # [NOTE]: sometimes the owner might no assign roles to themselves
        #         if they try to execute /kick, the bot will respond with:
        #         [You cannot kick someone with a higher or equal role ❗]
        #         This is why this line below must be implemented:
        #         interaction.user != interaction.guild.owner
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message(
                "You cannot kick someone with a higher or equal role ❗",
                ephemeral=True
            )
            return

        # Bot cannot kick someone with an equal or higher role
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "I cannot kick this member because their role is equal to or higher than my highest role.",
                ephemeral=True
            )
            return
        

        # Notify the kicked member first before kicking them
        try:
            await member.send(f"You have been kicked from **{member.guild.name}**\n**Reason**: {reason}\n{member.mention}")
        except (discord.Forbidden, discord.HTTPException):
            # If the kicked member has their DMs closed or the command failed, pass
            pass


        try:
            await member.kick(reason=f"Kicked by {interaction.user.name}: {reason}")
            await interaction.response.send_message(
                f"**{member.name}** has been kicked 🦶\n**Reason:** {reason}",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have the permission to kick this user.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Failed to kick {member.name}: {e}",
                ephemeral=True
            )

    @kick_member.error
    async def kick_member_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You need the `Kick Members` permission to use this command.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(ModConfig(bot))