from discord import SlashOption
import nextcord
from nextcord.ext import commands, application_checks


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
        description="Initializes the databases. (Owner only)",
    )
    @application_checks.is_owner()
    async def init(self, interaction: nextcord.Interaction):
        from .Warns import create_warn_table
        from other.wf.wfm_watchlist import create_wl_table

        await create_warn_table()
        await create_wl_table()
        await interaction.send("All databases initialized!")


def setup(bot):
    bot.add_cog(Admin(bot))
