from contextlib import redirect_stdout
import io
import textwrap
import traceback
from discord import SlashOption
import nextcord
from nextcord.ext import commands, application_checks


class EvalModal(nextcord.ui.Modal):
    def __init__(self, title: str, *, timeout=120):
        super().__init__(title, timeout=timeout)
        self.body = nextcord.ui.TextInput(
            label="The code to evaluate", style=nextcord.TextInputStyle.paragraph
        )
        self.add_item(self.body)

    async def callback(self, interaction: nextcord.Interaction):
        if self.body == "":
            return await interaction.send("You did not enter anything -> Cancelled!")

        body = self.body.value

        env = {
            "interaction": interaction,
            "bot": self.bot,
            "channel": interaction.channel,
            "author": interaction.user,
            "guild": interaction.guild,
            "message": interaction.message,
        }

        def cleanup_code(content):
            # remove ```py\n```
            if content.startswith("```") and content.endswith("```"):
                return "\n".join(content.split("\n")[1:-1])

            # remove `foo`
            return content.strip("` \n")

        env.update(globals())

        body = cleanup_code(body)
        stdout = io.StringIO()
        err = out = None

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        def paginate(text: str):
            last = 0
            pages = []
            for curr in range(0, len(text)):
                if curr % 1980 == 0:
                    pages.append(text[last:curr])
                    last = curr
                    appd_index = curr
            if appd_index != len(text) - 1:
                pages.append(text[last:curr])
            return list(filter(lambda a: a != "", pages))

        try:
            exec(to_compile, env)
        except Exception as e:
            err = await interaction.send(f"```py\n{e.__class__.__name__}: {e}\n```")
            return await interaction.message.add_reaction("\u2049")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            err = await interaction.send(f"```py\n{value}{traceback.format_exc()}\n```")
        else:
            value = stdout.getvalue()
            if ret is None:
                if value:
                    try:

                        out = await interaction.send(
                            f"Evaluated code:\n```py\n{body}\n```\nResult:\n```py\n{value}\n```"
                        )
                    except:
                        paginated_text = paginate(value)
                        first = True
                        for page in paginated_text:
                            info = (
                                "Evaluated code:\n```py\n{}\n```\nResult:\n".format(
                                    body
                                )
                                if first
                                else ""
                            )
                            if page == paginated_text[-1]:
                                out = await interaction.send(
                                    f"{info}```py\n{page}\n```"
                                )
                                break
                            await interaction.send(f"{info}```py\n{page}\n```")
                            first = False
            else:
                try:
                    out = await interaction.send(
                        f"Evaluated code:\n```py\n{body}\n```\nResult:\n```py\n{value}{ret}\n```"
                    )
                except:
                    paginated_text = paginate(f"{value}{ret}")
                    first = True
                    for page in paginated_text:
                        info = (
                            "Evaluated code:\n```py\n{}\n```\nResult:\n".format(body)
                            if first
                            else ""
                        )
                        if page == paginated_text[-1]:
                            out = await interaction.send(f"{info}```py\n{page}\n```")
                            break
                        await interaction.send(f"{info}```py\n{page}\n```")
                        first = False

        if out:
            await interaction.send("\u2705")  # tick
        elif err:
            await interaction.send("\u2049")  # x
        else:
            await interaction.send("\u2705")


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="admin", description="Commands for Bot Admins.")
    @application_checks.is_owner()
    async def admin(self, interaction: nextcord.Interaction):
        """Admin Commands"""
        pass

    @admin.subcommand(
        name="load", description="Loads a module. (Owner only)", inherit_hooks=True
    )
    async def load(self, interaction: nextcord.Interaction, *, module: str):
        """Loads a module."""
        try:
            self.bot.load_extension(module)
        except commands.ExtensionError as e:
            await interaction.send(f"{e.__class__.__name__}: {e}")
        else:
            await interaction.send("Done!")

    @admin.subcommand(
        name="unload", description="Unloads a module. (Owner only)", inherit_hooks=True
    )
    async def unload(self, interaction: nextcord.Interaction, *, module: str):
        """Unloads a module."""
        try:
            self.bot.unload_extension(module)
        except commands.ExtensionError as e:
            await interaction.send(f"{e.__class__.__name__}: {e}")
        else:
            await interaction.send("Done!")

    @admin.subcommand(
        name="reload", description="Reloads a module. (Owner only)", inherit_hooks=True
    )
    async def _reload(self, interaction: nextcord.Interaction, *, module: str):
        """Reloads a module."""
        try:
            self.bot.reload_extension(module)
        except commands.ExtensionError as e:
            await interaction.send(f"{e.__class__.__name__}: {e}")
        else:
            await interaction.send("Done!")

    @admin.subcommand(
        name="sync",
        description="Syncs all Slash Commands. (Owner only)",
        inherit_hooks=True,
    )
    async def _sync(self, interaction: nextcord.Interaction):
        try:
            await self.bot.sync_all_application_commands()
            await interaction.send("Synced all Application Commands!")
        except Exception as e:
            await interaction.send(f"{e.__class__.__name__}: {e}")

    @admin.subcommand(
        name="cp",
        description="Changes the Bot's presence. (Owner only)",
        inherit_hooks=True,
    )
    async def cp(
        self,
        interaction: nextcord.Interaction,
        text: str = SlashOption(
            name="text", description="The Bot's new presence text."
        ),
        mode: str = nextcord.SlashOption(
            name="mode",
            description="The method of changing the presence",
            choices=["add", "replace"],
            default="replace",
        ),
        status: str = nextcord.SlashOption(
            name="status",
            description="The new status.",
            choices={
                "online": "online",
                "offline": "offline",
                "idle": "idle",
                "dnd": "dnd",
            },
            default="online",
        ),
    ):
        statuses = {
            "online": nextcord.Status.online,
            "offline": nextcord.Status.offline,
            "idle": nextcord.Status.idle,
            "dnd": nextcord.Status.dnd,
        }
        s = statuses[status]
        if mode == "replace":
            await self.bot.change_presence(status=s, activity=nextcord.Game(text))
        elif mode == "add":
            pres = self.bot.activity.name
            await self.bot.change_presence(
                status=s, activity=nextcord.Game(pres + text)
            )
        await interaction.send(f"Presence changed!")

    @admin.subcommand(
        description="Initializes the databases. (Owner only)", inherit_hooks=True
    )
    async def init(self, interaction: nextcord.Interaction):
        from .Warns import create_warn_table
        from other.wf.wfm_watchlist import create_wl_table

        await create_warn_table()
        await create_wl_table()
        await interaction.send("All databases initialized!")

    @admin.subcommand(description="Evaluates a code.", name="eval", inherit_hooks=True)
    async def _eval(self, interaction: nextcord.Interaction):
        modal = EvalModal("Eval Code")
        modal.bot = self.bot
        await interaction.response.send_modal(modal)


def setup(bot):
    bot.add_cog(Admin(bot))
