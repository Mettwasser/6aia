from typing import Union
import nextcord, asqlite
from nextcord.ext import commands, application_checks
from nextcord.ext.commands.errors import (
    MissingPermissions,
)
from main import bot_basic_color
from other.utils import disable_buttons

# create the warn table, only needed once
async def create_warn_table():
    async with asqlite.connect("warns.db") as con:
        async with con.cursor() as cursor:
            await cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS warns (
                guild INT,
                mod INT,
                member INT,
                reason TEXT
            )
            """
            )


# creates a warn for a member
async def create_warn(
    interaction: nextcord.Interaction, member: Union[nextcord.Member, int], reason: str
):
    member = member.id if isinstance(member, nextcord.Member) else member
    async with asqlite.connect("warns.db") as con:
        async with con.cursor() as cursor:
            await cursor.execute(
                """
            INSERT INTO warns (guild, mod, member, reason)
            VALUES (?, ?, ?, ?)
            """,
                (interaction.guild.id, interaction.user.id, member, reason),
            )


# Gets the warns for a member
async def get_warns(
    interaction: nextcord.Interaction, member: Union[nextcord.Member, int]
):
    async with asqlite.connect("warns.db") as con:
        async with con.cursor() as cursor:
            member = member.id if isinstance(member, nextcord.Member) else member
            await cursor.execute(
                """
            SELECT rowid, * FROM warns
            WHERE guild = ? AND member = ?
            """,
                (interaction.guild.id, member),
            )

            # return a tuple of row objects, which can be accessed via column names
            return tuple(await cursor.fetchall())


# removes a warn for a member
async def remove_warn(rowid: int):
    async with asqlite.connect("warns.db") as con:
        async with con.cursor() as cursor:
            await cursor.execute(
                """
            DELETE FROM warns
            WHERE rowid = ?
            """,
                (rowid,),
            )


async def clear_warns(
    interaction: nextcord.Interaction, member: Union[nextcord.Member, int]
):
    async with asqlite.connect("warns.db") as con:
        async with con.cursor() as cursor:
            member = member.id if isinstance(member, nextcord.Member) else member
            await cursor.execute(
                """
            DELETE FROM warns
            WHERE member = ? AND guild = ?
            """,
                (member, interaction.guild.id),
            )


# checks if a member has the qualified permissions to use the warn commands
def removewarn_check(interaction: nextcord.Interaction, member: nextcord.Member):
    roles = member.roles
    role_ids = [r.id for r in roles]
    return (
        826194846393303150 in role_ids
        or interaction.user.guild_permissions.ban_members == True
        or interaction.user.guild_permissions.administrator == True
        or 774429158352486422 in role_ids
    )


# The buttons to be added to the warn-remove message
class WarnRemoveButton(nextcord.ui.Button):
    def __init__(self, warn_pos: int, rowid: int):
        super().__init__(style=nextcord.ButtonStyle.grey, label=f"{warn_pos}")
        self.rowid = rowid

    async def callback(self, interaction: nextcord.Interaction):
        await remove_warn(self.rowid)
        await self.update(interaction)

    async def update(self, interaction: nextcord.Interaction):
        # disable the button pressed, so it can't be pressed again and indicate that it was pressed by turning it red
        self.style = nextcord.ButtonStyle.red
        self.disabled = True
        self.view.removed_rowids.append(self.rowid)

        # Update the embed, to cross out removed warns
        member = interaction.guild.get_member(self.view.warns[0]["member"])
        embed = nextcord.Embed(
            description=f"{member.mention}'s warnings:",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        for c, warn in enumerate(self.view.warns, 1):
            mod = interaction.guild.get_member(warn["mod"])
            if mod is None:
                mod = await self.bot.fetch_user(warn["mod"])
                mod_str = f"{mod.name}#{mod.discriminator}"
            else:
                mod_str = mod.mention

            if warn["rowid"] in self.view.removed_rowids:
                embed.description += (
                    f"\n\n~~{c}. `{warn['reason']}`~~\n~~given by {mod_str}~~"
                )
            else:
                embed.description += f"\n\n{c}. `{warn['reason']}`\ngiven by {mod_str}"

        # check if all warns were removed, if so disable everything and stop listening to the view
        if all([x["rowid"] in self.view.removed_rowids for x in self.view.warns]):
            disable_buttons(self.view)
            self.view.stop()
        await interaction.response.edit_message(view=self.view, embed=embed)


# Own class to just not mess with the order of the buttons
class CancelButton(nextcord.ui.Button):
    def __init__(self):
        super().__init__(style=nextcord.ButtonStyle.red, label="Cancel")

    async def callback(self, interaction: nextcord.Interaction):
        disable_buttons(self.view)
        await interaction.response.edit_message(view=self.view)
        self.view.stop()


class WarnRemoveView(nextcord.ui.View):
    def __init__(
        self,
        interaction: nextcord.Interaction,  # for interaction_check
        warns: list,  # list of warns to be removed, is being parsed around
        *,
        timeout=45,
    ):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.warns = warns
        self.removed_rowids = []

        buttons = [WarnRemoveButton(c + 1, warn[0]) for c, warn in enumerate(warns)]

        for button in buttons:
            self.add_item(button)
        self.add_item(CancelButton())

    async def on_timeout(self) -> None:
        disable_buttons(self)
        await self.message.edit(view=self)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user != self.interaction.user:
            raise MissingPermissions("You haven't started this Command.")
        else:
            return True

    async def on_error(
        self,
        error: Exception,
        item: nextcord.ui.Item,
        interaction: nextcord.Interaction,
    ) -> None:
        if isinstance(error, MissingPermissions):
            await interaction.send(error.args[0], ephemeral=True)
        else:
            await interaction.send(
                f"{error}\n\nReport this to a developer.",
                ephemeral=True,
            )


class Warns(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @nextcord.slash_command(
        description="The prefix for all warn commands.",
        default_member_permissions=nextcord.Permissions(ban_members=True),
        guild_ids=[774313281543995402, 801922494390468648],
    )
    @application_checks.guild_only()
    async def warns(self, interaction: nextcord.Interaction):
        """Warn Command Prefix"""
        pass

    # Warns a user
    @warns.subcommand(
        description="Warns a member with the provided reason.", inherit_hooks=True
    )
    async def create(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            name="member", description="The member that will be warned."
        ),
        reason: str = nextcord.SlashOption(
            name="reason", description="The reason for the warn."
        ),
    ):
        await create_warn(interaction, member, reason)
        embed = nextcord.Embed(
            description=f"{member.mention} got warned for `{reason}`! This is their {len(await get_warns(interaction, member))}. warning!",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        await interaction.send(embed=embed)

    # Removes a warn
    @warns.subcommand(
        description="Deletes warns by clicking corresponding button. You do not need to delete multiple.",
        inherit_hooks=True,
    )
    async def remove(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            name="member",
            description="The member from which to delete warnings.",
        ),
    ):
        warns = await get_warns(interaction, member)
        if warns:
            embed = nextcord.Embed(
                description=f"{member.mention}'s warnings:",
                color=bot_basic_color,
                timestamp=nextcord.utils.utcnow(),
            )
            for c, warn in enumerate(warns, 1):
                mod = interaction.guild.get_member(warn["mod"])
                if mod is None:
                    mod = await self.bot.fetch_user(warn["mod"])
                    mod_str = f"{mod.name}#{mod.discriminator}"
                else:
                    mod_str = mod.mention
                embed.description += f"\n\n{c}. `{warn['reason']}`\ngiven by {mod_str}"

            view = WarnRemoveView(interaction, warns)
            view.message = await interaction.send(embed=embed, view=view)
        else:
            embed = nextcord.Embed(
                description=f"{member.mention} has no warnings!",
                color=bot_basic_color,
                timestamp=nextcord.utils.utcnow(),
            )
            await interaction.send(embed=embed)

    # Shows all warns of a user
    @warns.subcommand(
        description="Shows all the member's warnings.", inherit_hooks=True
    )
    async def show(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            name="member",
            description="The member whose warnings should be displayed.",
        ),
    ):
        warns = await get_warns(interaction, member)
        if warns:
            embed = nextcord.Embed(
                description=f"{member.mention} has the following {len(warns)} warnings:",
                color=bot_basic_color,
                timestamp=nextcord.utils.utcnow(),
            )
            for c, warn in enumerate(warns, 1):
                mod = interaction.guild.get_member(warn["mod"])
                if mod is None:
                    mod = await self.bot.fetch_user(warn["mod"])
                    mod_str = f"{mod.name}#{mod.discriminator}"
                else:
                    mod_str = mod.mention
                embed.description += f"\n\n{c}. `{warn['reason']}`\ngiven by {mod_str}"
        else:
            embed = nextcord.Embed(
                description=f"{member.mention} has no warnings!",
                color=bot_basic_color,
                timestamp=nextcord.utils.utcnow(),
            )

        await interaction.send(embed=embed)

    # Clears all warns of a user
    @warns.subcommand(
        description="Clears a member's warnings. This cannot be undone.",
        inherit_hooks=True,
    )
    async def clear(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            name="member",
            description="The member whose warns should be cleared.",
        ),
    ):
        await clear_warns(interaction, member)
        embed = nextcord.Embed(
            description=f"{member.mention}'s warnings have been cleared!",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(Warns(bot))
