from datetime import timedelta
import nextcord, re
from nextcord.ext import commands, application_checks
from main import bot_basic_color
from other.utils import to_timestamp
from other.HelpCmd import HelpCmd

# Check so e.g. Mods can't ban Admins
def member_is_higher(member1: nextcord.Member, member2: nextcord.Member):
    return member1.roles[-1] > member2.roles[-1]


# Time convertion (1h -> 3600s)
time_regex = re.compile(r"(\d{1,5}(?:[.,]?\d{1,5})?)([smhd])")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


def convert(argument):
    matches = time_regex.findall(argument.lower())
    time = 0
    for v, k in matches:
        try:
            time += time_dict[k] * float(v)
        except KeyError:
            raise KeyError("{} is an invalid time-key! h/m/s/d are valid!".format(k))
        except ValueError:
            raise ValueError("{} is not a number!".format(v))
    return time


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
            description="Choose a category at the bottom you want help for!",
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
