import discord
from discord import app_commands
from discord.ext import commands

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


async def setup(bot: commands.Bot):
    await bot.add_cog(MemberModeration(bot))