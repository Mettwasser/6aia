import nextcord
from discord import Forbidden
from nextcord.ext import commands, application_checks
from nextcord.errors import ApplicationCheckFailure, ApplicationInvokeError

from other.wf.Errors import APIError
from main import bot_basic_color

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_application_command_error(
        self, interaction: nextcord.Interaction, error
    ):

        if interaction.application_command.error_callback is not None:
            return
        
        # should always be raised
        if isinstance(error, ApplicationCheckFailure):

            # Missing perms
            if isinstance(error, application_checks.ApplicationMissingPermissions):
                m_perms = error.missing_permissions
                await interaction.send(
                    embed=nextcord.Embed(
                        title="Missing permissions",
                        description=f"You do not have the required permissions to use this command.\nRequired Permission{'s' if len(m_perms) > 1 else ''}: {', '.join(m_perms)}",
                        color=bot_basic_color
                    ),
                    ephemeral=True,
                )
                        
                await interaction.send(
                    embed=nextcord.Embed(
                        title="",
                        description="",
                        color=bot_basic_color
                    ),
                    ephemeral=True,
                )

            # fuck dms
            elif isinstance(error, application_checks.ApplicationNoPrivateMessage):
                await interaction.send(
                    embed=nextcord.Embed(
                        title="Not a DM command",
                        description="You cannot run this command in a DM Channel.",
                        color=bot_basic_color
                    ),
                    ephemeral=True,
                )

            # NotOwner
            elif isinstance(error, application_checks.ApplicationNotOwner):

                await interaction.send(
                    embed=nextcord.Embed(
                        title="Not the owner",
                        description="Only the Owner of the Bot is allowed to run this Command.",
                        color=bot_basic_color
                    ),
                    ephemeral=True,
                )

            elif isinstance(error, application_checks.ApplicationBotMissingPermissions):
                m_perms = error.missing_permissions
                await interaction.send(
                    embed=nextcord.Embed(
                        title="Bot missing permissions",
                        description=f"I do not have permissions for that. Check the role hierarchy or my permissions!\nRequired Permission{'s' if len(m_perms) > 1 else ''}: {', '.join(m_perms)}",
                        color=bot_basic_color
                    ),
                    ephemeral=True,
                )

            # Catches everything else
            else:
                await interaction.send(
                    f"```Ignoring exception in command {interaction.application_command}\n{type(error)} {error} {error.__traceback__}```\nReport this to a developer",
                    ephemeral=True,
                )
                await interaction.send(
                    embed=nextcord.Embed(
                        title="Error",
                        description=f"```Ignoring exception in command {interaction.application_command}\n{type(error)} {error} {error.__traceback__}```\nReport this to a developer",
                        color=bot_basic_color
                    ),
                    ephemeral=True,
                )

        elif isinstance(error, ApplicationInvokeError):
            error = error.original

            if isinstance(error, application_checks.ApplicationBotMissingPermissions):
                m_perms = error.missing_permissions
                await interaction.send(
                    embed=nextcord.Embed(
                        title="Bot missing permissions",
                        description=f"I do not have permissions for that. Check the role hierarchy or my permissions!\nRequired Permission{'s' if len(m_perms) > 1 else ''}: {', '.join(m_perms)}",
                        color=bot_basic_color
                    ),
                    ephemeral=True,
                )

            elif isinstance(error, application_checks.ApplicationMissingPermissions):
                m_perms = error.missing_permissions
                await interaction.send(
                    embed=nextcord.Embed(
                        title="Missing permissions",
                        description=f"You do not have the required permissions to use this command.\nRequired Permission{'s' if len(m_perms) > 1 else ''}: {', '.join(m_perms)}",
                        color=bot_basic_color
                    ),
                    ephemeral=True,
                )

            elif isinstance(error, Forbidden):

                await interaction.send(
                    embed=nextcord.Embed(
                        title="Bot missing permissions",
                        description=f"I do not have permissions for that. Check the role hierarchy or my permissions!",
                        color=bot_basic_color
                    ),
                    ephemeral=True,
                )

            if isinstance(error, APIError):
                await interaction.send(embed=nextcord.Embed(
                    title="API Error",
                    description="An error occured. This is probably due to an API error.",
                    color=bot_basic_color,
                    )
                )

            # Catches everything else
            else:
                await interaction.send(
                    f"```Ignoring exception in command {interaction.application_command}\n{type(error)} {error} {error.__traceback__}```\nReport to dev.",
                    ephemeral=True,
                )

        else:
            await interaction.send(
                f"```Ignoring exception in command {interaction.application_command}\n{type(error)} {error} {error.__traceback__}```\nReport to dev.",
                ephemeral=True,
            )

def setup(bot):
    bot.add_cog(ErrorHandler(bot))
