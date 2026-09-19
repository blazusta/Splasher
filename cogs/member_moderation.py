import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta

class MemberModeration(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
        # [NOTE]: sometimes the owner might not assign roles to themselves
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


    @app_commands.guild_only()
    @app_commands.command(name="ban", description="Ban a member from your server")
    @app_commands.describe(
        member="The member to ban", 
        delete_messages="Delete their messages from the last (0 - 7) days",
        reason="Reason for banning"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_member(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        delete_messages: app_commands.Range[int, 0, 7] = 0,
        reason: str = "No reason provided."
    ):
        
        # Hierarchy Validation

        if member == interaction.user:
            await interaction.response.send_message(
                "You cannot ban yourself!",
                ephemeral=True
            )
            return
        
        if member == interaction.guild.owner:
            await interaction.response.send_message(
                "You cannot ban the server owner!",
                ephemeral=True
            )
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message(
                "You cannot ban someone with a role higher than or equal to yours",
                ephemeral=True
            )
            return
        
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "I cannot ban someone with a higher or equal to my highest role!",
                ephemeral=True
            )
            return
        
        try:
            await member.send(f"You have been banned from {member.guild.name}\n**Reason:** {reason}\n{member.mention}")
        except (discord.Forbidden, discord.HTTPException):
            pass

        try:
            await member.ban(
                delete_message_seconds=delete_messages * 86400, 
                reason=f"Banned by {interaction.user.name}: {reason}"
            )
            await interaction.response.send_message(
                f"{member.name} has been banned!\n**Reason:** {reason}",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have the permission to ban this user.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Failed to ban this user: {e}",
                ephemeral=True
            )

    @ban_member.error
    async def ban_member_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You need the `Ban Members` permission to execute this command.",
                ephemeral=True
            )


    @app_commands.guild_only()
    @app_commands.command(name="unban", description="Unban a banned member")
    @app_commands.describe(user_id="The banned member ID to unban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban_member(
        self, 
        interaction: discord.Interaction,
        # Discord is built using JavaScript, which has a limit and cannot handle
        # numbers as big as discord IDs
        user_id: str, 
        reason: str = "No reason provided."
    ):
        
        if not user_id.isdigit():
            await interaction.response.send_message(
                "Invalid ID!, The ID must contain numbers only.",
                ephemeral=True
            )
            return
        
        # Convert the ID to an int
        user_object = discord.Object(int(user_id))

        try:
            ban_entry = await interaction.guild.fetch_ban(user_object)
            banned_user = ban_entry.user

            await interaction.guild.unban(
                banned_user,
                reason=f"Unbanned by {interaction.user.name}: {reason}"
            )

            await interaction.response.send_message(
                f"{banned_user.name} has been unbanned\n**Reason:** {reason}",
                ephemeral=True
            )
        except discord.NotFound:
            # if the banned user id was not found within the list of banned users
            await interaction.response.send_message(
                "This user is not banned from this server (or ID does not exist)",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have the permission to unban this user.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Failed to unban this user: {e}",
                ephemeral=True
            )

    @unban_member.error
    async def unban_member_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You do not have the `Ban Members` permission to execute this command.",
                ephemeral=True
            )


    @app_commands.guild_only()
    @app_commands.command(name="timeout", description="Disallow a member from sending messages for a period")
    @app_commands.describe(period="Period of timeout")
    @app_commands.choices(period=[
        app_commands.Choice(name="60 Seconds", value=60),
        app_commands.Choice(name="5 Minutes", value=300),
        app_commands.Choice(name="1 Hour", value=3600),
        app_commands.Choice(name="1 Day", value=86400),
        app_commands.Choice(name="1 Week", value=604800)
    ])
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout_member(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member,
        period: app_commands.Choice[int],
        reason: str = "No reason provided."
    ):
        
        if member.bot:
            await interaction.response.send_message(
                "You cannot execute this command on bots!",
                ephemeral=True
            )
            return
        
        if member == interaction.user:
            await interaction.response.send_message(
                "You cannot timeout yourself!",
                ephemeral=True
            )
            return
        
        if member == interaction.guild.owner:
            await interaction.response.send_message(
                "You cannot timeout the server owner!",
                ephemeral=True
            )
            return       
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message(
                "You cannot timeout someone with a role higher than or equal to yours",
                ephemeral=True
            )
            return
        
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "I cannot timeout this user because their role is higher than or equal to my highest role!",
                ephemeral=True
            )
            return
        
        try:
            duration = timedelta(seconds=period.value)
            await member.timeout(duration, reason=reason)
            await interaction.response.send_message(
                f"{member.mention} has been disallowed to send messages for {period.name}\n**Reason:** {reason}",
                ephemeral=True
            )

            try:
                await member.send(f"You have been disallowed to send messages for {period.name}\n**Reason:** {reason}\n{member.mention}")
            except (discord.Forbidden, discord.HTTPException):
                pass

        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have the permission to timeout this user.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Failed to timeout this user: {e}",
                ephemeral=True
            )

    @timeout_member.error
    async def timeout_member_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You do not have the `Moderate Members` permission to execute this command!",
                ephemeral=True
            )
        

    @app_commands.guild_only()
    @app_commands.command(name="untimeout", description="Revoke the timeout from a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout_member(
        self, 
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided."
    ):
        
        if member.bot:
            await interaction.response.send_message(
                "You cannot execute this command on bots!",
                ephemeral=True
            )
            return
        
        if not member.is_timed_out():
            await interaction.response.send_message(
                f"{member.mention} is not timed out!",
                ephemeral=True
            )
            return
        
        if member == interaction.user:
            await interaction.response.send_message(
                "You cannot untimeout yourself!",
                ephemeral=True
            )
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message(
                "You cannot untimeout this member because their role is higher than or equal to your highest role!",
                ephemeral=True
            )
            return
        
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "I cannot untimeout this member because their role is higher than or equal to my highest role!",
                ephemeral=True
            )
            return
        
        try:
            await member.timeout(None, reason=reason)
            await interaction.response.send_message(
                f"{member.mention} has been allowed to send messages in this server\n**Reason:** {reason}",
                ephemeral=True
            )

            try:
                await member.send(f"You can now send messages in {interaction.guild.name}\n**Reason:** {reason}\n{member.mention}")
            except (discord.Forbidden, discord.HTTPException):
                pass

        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have the permission to untimeout this user.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Failed to untimeout this user: {e}",
                ephemeral=True
            )

    @untimeout_member.error
    async def untimeout_member_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You do not have the `Moderate Members` permission to execute this command.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(MemberModeration(bot))