import nextcord
from nextcord.ext import commands
from main import bot_basic_color


class HelpDropdown(nextcord.ui.Select):
    def __init__(self):

        # Options
        options = [
            nextcord.SelectOption(
                label="General", description="Commands that aim at general use."
            ),
            nextcord.SelectOption(
                label="Warframe Commands", description="Commands related to Warframe."
            ),
        ]

        # min & max value = 1, so stuff can't intersect w eachother
        super().__init__(
            placeholder="Choose a category...",
            min_values=1,
            max_values=1,
            options=options,
        )

    # When the Dropdown gets clicked (as response), this func will be called
    # self.values[0] will always be the label of the item the user chose
    async def callback(self, interaction: nextcord.Interaction):

        embed = nextcord.Embed(
            title="",
            description="""
<> : required arguments
[x else y] : optional arguments
`y = the value when x is not given`\n\n
        """,
            color=bot_basic_color,
        )

        if self.values[0] == "General":
            embed.title = "General Commands"
            embed.description += """
**help** - shows this message.

**ping** - gives you the ping of the bot in milliseconds.

**emoji delete <emoji>** - deletes the Emoji by using it.

**emoji edit <emoji> <new-name>** - edits an emoji name.

**emoji steal by-usage <emoji>** - adds the used emoji on this Sever.

**emoji steal by-link <emoji-link> <name>** - adds the Emoji from the link you provided to this Server.
            """

        elif self.values[0] == "Warframe Commands":
            embed.title = "Warframe Commands"
            embed.description += """
**All Warframe-related commands start with the __/wf__ prefix.**

**fissures** [platform else pc] - shows you a list of all current fissures, sorted by efficiency.

**worldstates** - shows all current worldstates.

**baro** [platform else pc] - shows you a list of Baro's item or where and when he arrives.

**sortie** [platform else pc] - shows you the current sortie.

**invasions** [platform else pc] - shows you the current invasions.

**calculations enemy_hp/shields/armor/overguard/damage** <base-lvl> <current-lvl> [base else 1] - Calculate a scaling enemy stat by their base and current level. [base] is e.g. the base `HP` of an enemy.

**calculations enemy_affinity** <current-lvl> [base else 1] - same thing as above, except you do not need the base level for this.

**-- Related to warframe.market --**

**market search** <item_name> [platform else pc] [rank else 0] [filter else ingame] - searches for an item on [warframe.market](https://warframe.market). All tradable items should have an autocompletion. [rank] does only work on items like Arcanes and Mods. [filter] filters search results based on the seller's status.

**market searchmany** <item_name> <amount to look up> [platform else pc] [rank else 0] [filter else ingame] - searches for multiple items on [warframe.market](https://warframe.market). All tradable items should have an autocompletion. [rank] does only work on items like Arcanes and Mods. [filter] filters search results based on the seller's status.

**market average** <item_name> [platform else pc] [rank else 0] - gets the average price for an item on [warframe.market](https://warframe.market). All tradable items should have an autocompletion. [rank] does only work on items like Arcanes and Mods.

**watchlist add** <item_name> [platform else pc] [rank else 0] - adds an item to your watchlist. [rank] does only work on items like Arcanes and Mods.

**watchlist remove** - removes items from your watchlist.

**watchlist show** - shows all the items in your watchlist.

**watchlist clear** - clears your watchlist.

**watchlist calc** - calculates the average price of all items in your watchlist. (includes Rank)

**watchlist export** - exports your watchlist as a text file.
            """

        # Edit the message and set the text to the chosen category
        self.placeholder = self.values[0]
        await interaction.response.edit_message(embed=embed, view=self.view)


# Button to cancel the cmd
class HelpCancelButton(nextcord.ui.Button):
    def __init__(self, row=None):
        super().__init__(style=nextcord.ButtonStyle.red, label="Cancel", row=row)

    # on callback, clear the items & stop listening to the View
    async def callback(self, interaction: nextcord.Interaction):
        self.view.clear_items()
        await interaction.response.edit_message(view=self.view)
        self.view.stop()


# Help View
class HelpCmd(nextcord.ui.View):
    def __init__(self, initial_interaction: nextcord.Interaction, *, timeout=35):
        super().__init__(timeout=timeout)

        # Add initial 2 items
        self.add_item(HelpDropdown())
        self.add_item(HelpCancelButton())

        # To edit the message in on_timeout and do a proper check
        self.initial_interaction = initial_interaction

    async def on_timeout(self) -> None:
        self.clear_items()
        await self.msg.edit(view=self)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        # if the command author is the one who interacted, let it pass
        if self.initial_interaction.user == interaction.user:
            return True

        # if not, raise MissingPerms
        raise commands.errors.MissingPermissions(
            "You cannot interact with a help menu that was called by someone else."
        )

    # Catch MissingPerms here
    async def on_error(
        self,
        error: Exception,
        item: nextcord.ui,
        interaction: nextcord.Interaction,
    ) -> None:
        if isinstance(error, commands.errors.MissingPermissions):
            await interaction.send(
                embed=nextcord.Embed(
                    title="Error",
                    description=error.args[0],
                    color=bot_basic_color,
                ),
                ephemeral=True,
            )

        else:
            await interaction.send(
                embed=nextcord.Embed(
                    title="Error",
                    description=f"{error}\n\nReport this to a developer.",
                    color=bot_basic_color,
                ),
                ephemeral=True,
            )
