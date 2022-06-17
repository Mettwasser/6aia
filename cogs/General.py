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

    # Timeout Command
    @nextcord.slash_command(
        description="Timeouts a member.",
        default_member_permissions=nextcord.Permissions(moderate_members=True),
    )
    @application_checks.guild_only()
    async def timeout(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            name="user", description="The user to timeout"
        ),
        time: str = nextcord.SlashOption(
            name="time", description="The time the User will be timouted (eg. 6h)"
        ),
    ):
        # convert 1d -> seconds, 1.5h works aswell, so does 1h30m
        # using regex
        td = timedelta(seconds=convert(time))

        # add timeout to member
        await member.edit(timeout=td)

        # send confirmation msg
        embed = nextcord.Embed(
            title=f"{member.name} has been timeouted!",
            description=f"{member.mention} has been timeouted until {to_timestamp(nextcord.utils.utcnow() + td)}.",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
