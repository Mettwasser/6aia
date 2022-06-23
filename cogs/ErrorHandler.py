import nextcord
from nextcord.ext import commands, application_checks
from nextcord.errors import ApplicationCheckFailure, ApplicationInvokeError


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_application_command_error(
        self, interaction: nextcord.Interaction, error
    ):

        # should always be raised
        if isinstance(error, ApplicationCheckFailure):

            # Missing perms
            if isinstance(error, application_checks.ApplicationMissingPermissions):
                m_perms = error.missing_permissions
                await interaction.send(
                    f"You do not have the required permissions to use this command.\n"
                    f"Required Permission{'s' if len(m_perms) > 1 else ''}: {', '.join(m_perms)}"
                )

            # fuck dms
            elif isinstance(error, application_checks.ApplicationNoPrivateMessage):
                await interaction.send("You cannot run this command in a DM CHannel.")

            # NotOwner
            elif isinstance(error, application_checks.ApplicationNotOwner):
                await interaction.send(
                    "Only the Owner of the Bot is allowed to run this Command."
                )

            elif isinstance(error, application_checks.ApplicationBotMissingPermissions):
                await interaction.send(
                    "I do not have permissions for that. Check the role hierarchy or my permissions!"
                )

            # Catches everything else
            else:
                await interaction.send(
                    f"```Ignoring exception in command {interaction.application_command}\n{type(error)} {error} {error.__traceback__}```\nReport to dev.",
                    ephemeral=True,
                )

        elif isinstance(error, ApplicationInvokeError):
            error = error.original

            if isinstance(error, application_checks.ApplicationBotMissingPermissions):
                await interaction.send(
                    "I do not have permissions for that. Check the role hierarchy or my permissions!"
                )

            elif isinstance(error, application_checks.ApplicationMissingPermissions):
                m_perms = error.missing_permissions
                await interaction.send(
                    f"You do not have the required permissions to use this command.\n"
                    f"Required Permission{'s' if len(m_perms) > 1 else ''}: {', '.join(m_perms)}"
                )

            # Catches everything else
            else:
                print("Error handled")
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
