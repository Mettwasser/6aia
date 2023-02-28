import nextcord
from nextcord.ext import commands, application_checks
from main import bot_basic_color
from other.HelpCmd import HelpCmd


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Help Command
    @nextcord.slash_command(name="help", description="Gives you a help menu.")
    @application_checks.guild_only()
    async def help(self, interaction: nextcord.Interaction):

        # Help View with all its components
        view = HelpCmd(interaction)
        embed = nextcord.Embed(
            title="Help Menu",
            description="Choose a category at the bottom you want help for!\nData Provided by the [Warframe Community Developers](https://docs.warframestat.us) and [warframe.market](https://warframe.market)\n\nJoin the support server **[here](https://discord.gg/paAyF8A)**!",
            color=bot_basic_color,
        )
        view.msg = await interaction.send(embed=embed, view=view)

    # Ping Command
    @nextcord.slash_command(description="Shows you the Ping.")
    @application_checks.guild_only()
    async def ping(self, interaction: nextcord.Interaction):

        # Send the Embed
        await interaction.send(
            embed=nextcord.Embed(
                title="Pong!",
                description=f"{int(self.bot.latency * 1000)}ms",
                color=bot_basic_color,
            )
        )


def setup(bot):
    bot.add_cog(General(bot))
