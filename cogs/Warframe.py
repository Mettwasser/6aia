import nextcord, requests, aiohttp, difflib
from nextcord.ext import commands
from main import bot_basic_color
from other.wf import *
from other.utils import align

# Item list for "autocompletion"
HOST = "https://api.warframe.market/v1"
item_dict = requests.get(HOST + "/items").json()["payload"]["items"]
item_names = [x["item_name"] for x in item_dict]


def set_item_urlname(item_name: str):

    name = difflib.get_close_matches(
        item_name.capitalize(), [x["item_name"] for x in item_dict]
    )
    if name:
        return name[0].lower().replace(" ", "_")
    return None


async def wfm_autocomplete(cog, interaction: nextcord.Interaction, kwarg: str):
    if not kwarg:
        # send the full autocomplete list
        await interaction.response.send_autocomplete(item_names[0:24])
        return
    # send a list of nearest matches from the list of dog breeds
    autocompletes = [
        item for item in item_names if item.lower().startswith(kwarg.lower())
    ]
    await interaction.response.send_autocomplete(autocompletes[0:24])


class Warframe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(description="Warframe Command Prefix", name="wf")
    async def wf(self, interaction: nextcord.Interaction):
        # pass, this is just the command prefix, so we don't need to do anything
        pass

    @wf.subcommand(
        name="market",
        description="Warframe commands, that are related to warframe.market.",
    )
    async def market(self, interaction: nextcord.Interaction):
        # another base for subcommands
        pass

    # Market Search
    @market.subcommand(description="Searches for an item on warframe.market.")
    async def search(
        self,
        interaction: nextcord.Interaction,
        actual_name: str = nextcord.SlashOption(
            name="item_name",
            description="The item name to search for",
            autocomplete_callback=wfm_autocomplete,
        ),
        platform: str = nextcord.SlashOption(
            name="platform",
            description="The platform you're playing on.",
            choices={
                "playstation": "ps4",
                "xbox": "xbox",
                "pc": "pc",
                "switch": "switch",
            },
            default="pc",
        ),
        mod_rank: int = nextcord.SlashOption(
            name="rank",
            description="The (mod) rank to search for",
            default=0,
        ),
        search_filter: str = nextcord.SlashOption(
            name="filter",
            description="A filter that is applied to the status of players.",
            choices=["ingame", "offline", "all"],
            default="ingame",
        ),
    ):
        url_name = set_item_urlname(actual_name)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    "https://api.warframe.market/v1/items/{}/orders?include=item".format(
                        url_name.lower()
                    ),
                    headers={"Platform": platform},
                    params={"include": "item"},
                ) as resp:
                    if resp.status == 200:
                        json_content = await resp.json()
                    else:
                        await interaction.send(
                            "Something went wrong. This is probably due to an API Error."
                        )
                        return

                await check_mod_rank(session, url_name, mod_rank)
                embed = single_search_form_embed(
                    search_filter,
                    mod_rank,
                    json_content,
                    url_name,
                )
                await interaction.send(content=None, embed=embed)

            except KeyError:
                await interaction.send(
                    f"I was unable to find the item `({actual_name})` you were trying to search. Please make sure to have the correct `spelling` of the item you want to search up."
                )

            except IndexError:
                await interaction.send(
                    f"{actual_name} has no listings! (filter: {search_filter}{', rank: {}'. format(mod_rank) if await is_mod(url_name, session) else ''})"
                )

            except AttributeError:
                await interaction.send(
                    f"I was unable to find the item `({actual_name})` you were trying to search. Please make sure to have the correct `spelling` of the item you want to search up."
                )

            except ModRankError as e:
                await interaction.send(
                    f"The rank you entered is higher than the maximum rank of this item.\n`Max. Rank for {actual_name}: {e.args[0]}`"
                )

    # Market Search
    @market.subcommand(description="Searches multiple items on warframe.market.")
    async def searchmany(
        self,
        interaction: nextcord.Interaction,
        actual_name: str = nextcord.SlashOption(
            name="item_name",
            description="The item name to search for",
            autocomplete_callback=wfm_autocomplete,
        ),
        amount_to_look_up: int = nextcord.SlashOption(
            name="amount-to-look-up", description="The amount of orders to look up."
        ),
        platform: str = nextcord.SlashOption(
            name="platform",
            description="The platform you're playing on.",
            choices={
                "playstation": "ps4",
                "xbox": "xbox",
                "pc": "pc",
                "switch": "switch",
            },
            default="pc",
        ),
        mod_rank: int = nextcord.SlashOption(
            name="rank",
            description="The (mod) rank to search for",
            default=0,
        ),
        search_filter: str = nextcord.SlashOption(
            name="filter",
            description="A filter that is applied to the status of players.",
            choices=["ingame", "offline", "all"],
            default="ingame",
        ),
    ):
        url_name = set_item_urlname(actual_name)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    "https://api.warframe.market/v1/items/{}/orders?include=item".format(
                        url_name.lower()
                    ),
                    headers={"Platform": platform},
                    params={"include": "item"},
                ) as resp:
                    if resp.status == 200:
                        json_content = await resp.json()

                    else:
                        await interaction.send(
                            "Something went wrong. This is probably due to an API Error."
                        )
                        return

                await check_mod_rank(session, url_name, mod_rank)

                view = WFBrowser(
                    json_content,
                    amount_to_look_up,
                    actual_name,
                    url_name,
                    interaction,
                    search_filter,
                    mod_rank,
                )

                try:
                    initial_embed = (
                        view.form_embed()
                        if view.max_orders > 1
                        else single_search_form_embed(
                            self.search_filter,
                            self.mod_rank,
                            self.json_content,
                            self.item_name,
                        )
                    )
                except IndexError as e:
                    raise e
                if view.max_orders > 1:
                    view.msg = await interaction.send(embed=initial_embed, view=view)
                else:
                    await interaction.send(embed=initial_embed)

            except KeyError:
                await interaction.send(
                    f"I was unable to find the item `({actual_name})` you were trying to search. Please make sure to have the correct `spelling` of the item you want to search up."
                )

            except IndexError:
                await interaction.send(
                    f"{actual_name} has no listings! (filter: {search_filter}{', rank: {}'. format(mod_rank) if await is_mod(url_name, session) else ''})"
                )

            except AttributeError:
                await interaction.send(
                    f"I was unable to find the item `({actual_name})` you were trying to search. Please make sure to have the correct `spelling` of the item you want to search up."
                )

            except ModRankError as e:
                await interaction.send(
                    f"The rank you entered is higher than the maximum rank of this item.\n`Max. Rank for {actual_name}: {e.args[0]}`"
                )

    # Gets the Average price for an Item
    @market.subcommand(
        description="Gives you the average price of an item on warframe.market."
    )
    async def avg(
        self,
        interaction: nextcord.Interaction,
        actual_name: str = nextcord.SlashOption(
            name="item_name",
            description="The item name to search for",
            autocomplete_callback=wfm_autocomplete,
        ),
        platform: str = nextcord.SlashOption(
            name="platform",
            description="The platform you're playing on.",
            choices={
                "playstation": "ps4",
                "xbox": "xbox",
                "pc": "pc",
                "switch": "switch",
            },
            default="pc",
        ),
        mod_rank: int = nextcord.SlashOption(
            name="rank",
            description="The (mod) rank to search for",
            default=0,
        ),
    ):
        url_name = set_item_urlname(actual_name)
        try:
            item_is_mod = await is_mod(url_name)
            avg_price, total_sales, moving_avg = await get_avg(
                platform, url_name, actual_name, mod_rank
            )
            embed = nextcord.Embed(color=bot_basic_color)
            embed.title = f"Average price of {to_item_name(url_name)} {'(R{})'.format(mod_rank) if item_is_mod else ''}"
            embed.description = f"Average price: **{avg_price}**\n**{total_sales}** sales in the last 48 hours\nMoving average: **{moving_avg}**"
            await interaction.send(embed=embed)

        except KeyError:
            await interaction.send(
                f"I was unable to find the item `({actual_name})` you were trying to search. Please make sure to have the correct `spelling` of the item you want to search up."
            )

        except IndexError as e:
            await interaction.send(e.args[0])

        except ModRankError as e:
            await interaction.send(
                f"The rank you entered is higher than the maximum rank of this item.\n`Max. Rank for {actual_name}: {e.args[0]}`"
            )

    # WATCHLIST STUFF

    @wf.subcommand(
        name="watchlist", description="Subcommand Group for the watchlist commands."
    )
    async def watchlist(self, interaction: nextcord.Interaction):
        pass

    @watchlist.subcommand(
        name="add",
        description="Adds an item to your watchlist. Limited to 3 items.",
    )
    async def _wl_add(
        self,
        interaction: nextcord.Interaction,
        actual_name: str = nextcord.SlashOption(
            name="item_name",
            description="The item name to search for",
            autocomplete_callback=wfm_autocomplete,
        ),
        platform: str = nextcord.SlashOption(
            name="platform",
            description="The platform you're playing on.",
            choices={
                "playstation": "ps4",
                "xbox": "xb1",
                "pc": "pc",
                "switch": "swi",
            },
            default="pc",
        ),
        mod_rank: int = nextcord.SlashOption(
            name="rank",
            description="The (mod) rank to search for",
            default=0,
        ),
    ):
        url_name = set_item_urlname(actual_name)
        items = await get_wl_items(interaction)
        if len(items) >= 3:
            return await interaction.send(
                "You can only have 3 items to your watchlist!"
            )
        try:
            async with aiohttp.ClientSession() as session:
                await check_mod_rank(session, url_name, mod_rank)
                item_is_mod = await is_mod(url_name, session)

        except KeyError:
            return await interaction.send(
                f"I was unable to find the item `({actual_name})` you were trying to search. Please make sure to have the correct `spelling` of the item you want to search up."
            )
        except ModRankError as e:
            return await interaction.send(
                f"The rank you entered is higher than the maximum rank of this item.\n`Max. Rank for {actual_name}: {e.args[0]}`"
            )

        if items:
            platform = items[0]["platform"]

        await wl_add(
            interaction,
            url_name,
            platform,
            mod_rank,
            "TRUE" if item_is_mod else "FALSE",
        )
        embed = nextcord.Embed(
            title="Item Added!",
            description=f"{actual_name}{' (Rank {})'.format(mod_rank) if item_is_mod else ''} added to your watchlist!",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        await interaction.send(embed=embed)

    @watchlist.subcommand(
        name="remove", description="Removes items from your watchlist."
    )
    async def _wl_remove(self, interaction: nextcord.Interaction):
        items = await get_wl_items(interaction)

        if not items:
            embed = nextcord.Embed(
                description=f"Your Watchlist is Empty!",
                color=bot_basic_color,
                timestamp=nextcord.utils.utcnow(),
            )
            return await interaction.send(embed=embed)

        view = WLRemoveView(interaction, items)
        embed = nextcord.Embed(
            title=f"Your Watchlist ({items[0]['platform']}):",
            description="",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        for c, item in enumerate(items, 1):
            embed.description += f"\n\n{c}. `{to_item_name(item['url_name'])}{' (R{})'.format(item['mod_rank']) if await wl_is_mod(interaction, item['url_name']) else ''}`"

        view.message = await interaction.send(embed=embed, view=view)

    @watchlist.subcommand(
        name="calc",
        description="Shows the average prices of all your watchlist items.",
    )
    async def wl_calc(self, interaction: nextcord.Interaction):
        items = await get_wl_items(interaction)
        if not items:
            embed = nextcord.Embed(
                description=f"Your Watchlist is Empty!",
                color=bot_basic_color,
                timestamp=nextcord.utils.utcnow(),
            )
            return await interaction.send(embed=embed)
        embed = await build_embed(interaction)
        await interaction.send(embed=embed)

    @watchlist.subcommand(name="clear", description="Clears your watchlist.")
    async def _wl_clear(self, interaction: nextcord.Interaction):
        items = await get_wl_items(interaction)
        if not items:
            embed = nextcord.Embed(
                description=f"Your Watchlist is Empty!",
                color=bot_basic_color,
                timestamp=nextcord.utils.utcnow(),
            )
            return await interaction.send(embed=embed)

        await clear_wl_items(interaction)
        embed = nextcord.Embed(
            title="Watchlist Cleared!",
            description="Your watchlist has been cleared!",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        await interaction.send(embed=embed)

    @watchlist.subcommand(name="show", description="Shows your watchlist.")
    async def _wl_show(self, interaction: nextcord.Interaction):
        items = await get_wl_items(interaction)
        if not items:
            embed = nextcord.Embed(
                description=f"Your Watchlist is Empty!",
                color=bot_basic_color,
                timestamp=nextcord.utils.utcnow(),
            )
            return await interaction.send(embed=embed)

        embed = nextcord.Embed(
            title="Your Watchlist:",
            description="",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        for c, item in enumerate(items, 1):
            embed.description += f"\n\n{c}. `{to_item_name(item['url_name'])}{' (R{})'.format(item['mod_rank']) if await wl_is_mod(interaction, item['url_name']) else ''}`"

        await interaction.send(embed=embed)

    @watchlist.subcommand(
        name="export", description="Exports your watchlist as txt file (calculated)."
    )
    async def _wl_export(self, interaction: nextcord.Interaction):
        items = await get_wl_items(interaction)
        if not items:
            embed = nextcord.Embed(
                description=f"Your Watchlist is Empty!",
                color=bot_basic_color,
                timestamp=nextcord.utils.utcnow(),
            )
            return await interaction.send(embed=embed)

        file = await export_as_file(interaction)
        await interaction.send(file=file)

    # fissures
    @wf.subcommand(
        name="fissures",
        description="Shows you all active fissures and sorts them by efficiency.",
    )
    async def fissures(
        self,
        interaction: nextcord.Interaction,
        platform: str = nextcord.SlashOption(
            name="platform",
            description="The platform you're playing on.",
            choices={
                "playstation": "ps4",
                "xbox": "xb1",
                "pc": "pc",
                "switch": "swi",
            },
            default="pc",
        ),
    ):
        active = await vf(platform)
        efficient = active["should"] if isinstance(active, dict) else None
        inefficient = active["shouldnt"] if isinstance(active, dict) else active

        embed = nextcord.Embed(
            title=f"Active Fissures ({platform})",
            description="**Fissures you SHOULD run:**\n\n{}\n\n\n**Fissures you SHOULDN'T run:**\n\n{}".format(
                "\n".join(efficient), "\n".join(inefficient)
            )
            if efficient is not None
            else "**All Fissures**:{}".format("\n".join(inefficient)),
            color=bot_basic_color,
        )
        embed.set_thumbnail(
            url="https://static.wikia.nocookie.net/warframe/images/a/ae/VoidProjectionsIronD.png/revision/latest?cb=20160709035804"
        )

        await interaction.send(embed=embed)

    # WORLD STATES
    @wf.subcommand(name="worldstates", description="Shows you all worldstates.")
    async def _worldstates(self, interaction: nextcord.Interaction):
        embed = await cycles()
        await interaction.send(embed=embed)

    @wf.subcommand(
        name="baro", description="Shows you Baro's inventory or when he returns."
    )
    async def baro(
        self,
        interaction: nextcord.Interaction,
        platform: str = nextcord.SlashOption(
            name="platform",
            description="The platform you're playing on.",
            choices={
                "playstation": "ps4",
                "xbox": "xb1",
                "pc": "pc",
                "switch": "swi",
            },
            default="pc",
        ),
    ):

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.warframestat.us/{platform}/voidTrader/",
                headers={"language": "en"},
            ) as resp:
                if resp.status != 200:
                    embed = nextcord.Embed(
                        title="Error",
                        description="Something went wrong while fetching the data! This is most likely an API error.",
                        color=bot_basic_color,
                    )
                    return await interaction.send(embed=embed)
                json_content = await resp.json()

        inventory = json_content["inventory"]

        if not inventory:
            embed = nextcord.Embed(
                title="Baro is not here yet!",
                description=f"**Time until Baro arrives at {json_content['location']}**\n{json_content['startString']}",
                color=bot_basic_color,
            )
            return await interaction.send(embed=embed)

        embed = nextcord.Embed(
            title="Baro's Inventory",
            description="",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        for item in inventory:
            embed.add_field(
                name=item["item"],
                value=f"<:ducats:885579733939667024> {item['ducats']}\n<:credits:885576185034194954> {item['credits']}",
            )
        embed.set_thumbnail(
            url="https://static.wikia.nocookie.net/warframe/images/a/a7/TennoCon2020BaroCropped.png/revision/latest/scale-to-width-down/350?cb=20200712232455"
        )
        embed.url = "https://warframe.fandom.com/wiki/Baro_Ki%27Teer"
        await interaction.send(embed=embed)

    @wf.subcommand(name="sortie", description="Shows you the current sortie.")
    async def sortie(
        self,
        interaction: nextcord.Interaction,
        platform: str = nextcord.SlashOption(
            name="platform",
            description="The platform you're playing on.",
            choices={
                "playstation": "ps4",
                "xbox": "xb1",
                "pc": "pc",
                "switch": "swi",
            },
            default="pc",
        ),
    ):
        embed = await sortie_embed(platform)
        await interaction.send(embed=embed)

    @wf.subcommand(name="invasions", description="Shows you the current invasions.")
    async def invasions(
        self,
        interaction: nextcord.Interaction,
        platform: str = nextcord.SlashOption(
            name="platform",
            description="The platform you're playing on.",
            choices={
                "playstation": "ps4",
                "xbox": "xb1",
                "pc": "pc",
                "switch": "swi",
            },
            default="pc",
        ),
    ):
        embed = await invasion_embed(platform)
        await interaction.send(embed=embed)

    @wf.subcommand(
        name="arbi", description="Shows you the current Arbitration. (Unstable)"
    )
    async def arbi(
        self,
        interaction: nextcord.Interaction,
        platform: str = nextcord.SlashOption(
            name="platform",
            description="The platform you're playing on.",
            choices={
                "playstation": "ps4",
                "xbox": "xb1",
                "pc": "pc",
                "switch": "swi",
            },
            default="pc",
        ),
    ):
        embed = await build_arbi_embed(platform)
        await interaction.send(embed=embed)

    @wf.subcommand(
        name="calculations",
        description="Subcommand Base for Calculations related to Warframe.",
    )
    async def calculations(self, interaction: nextcord.Interaction):
        pass

    @calculations.subcommand(
        name="ehp",
        description="Calculate the EHP of Health/Armor/DR/Damage Type Modifiers.",
    )
    async def ehp(
        self,
        interaction: nextcord.Interaction,
        health: int = nextcord.SlashOption(
            name="health", description="The Health that would display on your Warframe."
        ),
        armor: int = nextcord.SlashOption(
            name="armor",
            description="The armor you want to apply on this calculation.",
            default=0,
            required=False,
        ),
        drp: str = nextcord.SlashOption(
            name="damage-reduction",
            description="The damage reduction you currently have in %. (e.g. `90%`)",
            default="0%",
            required=False,
        ),
        dmp: str = nextcord.SlashOption(
            name="damage-modifier",
            description="The damage modifier you currently have in %. (e.g. `75%`)",
            default="0%",
            required=False,
        ),
    ):
        effective_hp = calc_ehp(
            health,
            armor=armor,
            damage_reduction_percentage=drp,
            damage_modifier_percentage=dmp,
        )

        names = ["Health", "Armor", "Damage Reduction", "Damage Modifier"]
        values = [health, armor, drp, dmp]
        desc = align(names, values)

        embed = nextcord.Embed(
            title="Effective Hit Points",
            description=f"Specs:\n```\n{desc}\n```\nCalculated EHP: **{effective_hp}**",
            color=bot_basic_color,
        )
        await interaction.send(embed=embed)

    @calculations.subcommand(
        name="enemy_hp", description="Calculates the Enemy HP based on their level."
    )
    async def _enemy_hp(
        self,
        interaction: nextcord.Interaction,
        base_level: int = nextcord.SlashOption(name="base-lvl", description="The Base level of the enemy."),
        current_level: int = nextcord.SlashOption(name="current-lvl", description="The Current level of the enemy."),
        hp: int = nextcord.SlashOption(name="base-hp", description="The Base hp of the enemy.", required=False, default=1),
    ):
        enemy = EnemyHP(base_level, current_level, hp)
        enemy_hp = human_format(enemy.calc())
        names = ["Base level", "Current Level", "Base HP"]
        values = [base_level, current_level, hp]
        desc = align(names, values)

        embed = nextcord.Embed(
            title="Enemy HP",
            description=f"Specs:\n```\n{desc}\n```\nCalculated Enemy HP: **{enemy_hp}**",
            color=bot_basic_color,
        )
        await interaction.send(embed=embed)

    @calculations.subcommand(
        name="enemy_shields", description="Calculates the Enemy Shields based on their level."
    )
    async def _enemy_shields(
        self,
        interaction: nextcord.Interaction,
        base_level: int = nextcord.SlashOption(name="base-lvl", description="The Base level of the enemy."),
        current_level: int = nextcord.SlashOption(name="current-lvl", description="The Current level of the enemy."),
        shields: int = nextcord.SlashOption(name="base-shields", description="The Base Shields of the enemy.", required=False, default=1),
    ):
        enemy = EnemyShields(base_level, current_level, shields)
        enemy_shields = human_format(enemy.calc())
        names = ["Base level", "Current Level", "Base Shields"]
        values = [base_level, current_level, shields]
        desc = align(names, values)

        embed = nextcord.Embed(
            title="Enemy Shields",
            description=f"Specs:\n```\n{desc}\n```\nCalculated Enemy Shields: **{enemy_shields}**",
            color=bot_basic_color,
        )
        await interaction.send(embed=embed)

    @calculations.subcommand(
        name="enemy_armor", description="Calculates the Enemy Armor based on their level."
    )
    async def _enemy_armor(
        self,
        interaction: nextcord.Interaction,
        base_level: int = nextcord.SlashOption(name="base-lvl", description="The Base level of the enemy."),
        current_level: int = nextcord.SlashOption(name="current-lvl", description="The Current level of the enemy."),
        armor: int = nextcord.SlashOption(name="base-armor", description="The Base armor of the enemy.", required=False, default=1),
    ):
        enemy = EnemyArmor(base_level, current_level, armor)
        enemy_armor = human_format(enemy.calc())
        names = ["Base level", "Current Level", "Base Armor"]
        values = [base_level, current_level, armor]
        desc = align(names, values)

        embed = nextcord.Embed(
            title="Enemy Armor",
            description=f"Specs:\n```\n{desc}\n```\nCalculated Enemy Armor: **{enemy_armor}**",
            color=bot_basic_color,
        )
        await interaction.send(embed=embed)

    @calculations.subcommand(
        name="enemy_overguard", description="Calculates the Enemy Overguard based on their level."
    )
    async def _enemy_overguard(
        self,
        interaction: nextcord.Interaction,
        base_level: int = nextcord.SlashOption(name="base-lvl", description="The Base level of the enemy."),
        current_level: int = nextcord.SlashOption(name="current-lvl", description="The Current level of the enemy."),
        overguard: int = nextcord.SlashOption(name="base-overguard", description="The Base Overguard of the enemy.", required=False, default=1),
    ):
        enemy = EnemyOverguard(base_level, current_level, overguard)
        enemy_overguard = human_format(enemy.calc())
        names = ["Base level", "Current Level", "Base Overguard"]
        values = [base_level, current_level, overguard]
        desc = align(names, values)

        embed = nextcord.Embed(
            title="Enemy Overguard",
            description=f"Specs:\n```\n{desc}\n```\nCalculated Enemy Overguard: **{enemy_overguard}**",
            color=bot_basic_color,
        )
        await interaction.send(embed=embed)

    @calculations.subcommand(
        name="enemy_damage", description="Calculates the Enemy Damage based on their level."
    )
    async def _enemy_damage(
        self,
        interaction: nextcord.Interaction,
        base_level: int = nextcord.SlashOption(name="base-lvl", description="The Base level of the enemy."),
        current_level: int = nextcord.SlashOption(name="current-lvl", description="The Current level of the enemy."),
        damage: int = nextcord.SlashOption(name="base-damage", description="The Base Damage of the enemy.", required=False, default=1),
    ):
        enemy = EnemyDamage(base_level, current_level, damage)
        enemy_damage = human_format(enemy.calc())
        names = ["Base level", "Current Level", "Base Damage"]
        values = [base_level, current_level, damage]
        desc = align(names, values)

        embed = nextcord.Embed(
            title="Enemy Damage",
            description=f"Specs:\n```\n{desc}\n```\nCalculated Enemy Damage: **{enemy_damage}**",
            color=bot_basic_color,
        )
        await interaction.send(embed=embed)

    @calculations.subcommand(
        name="enemy_affinity", description="Calculates the Enemy Affinity based on their level."
    )
    async def _enemy_affinity(
        self,
        interaction: nextcord.Interaction,
        current_level: int = nextcord.SlashOption(name="current-lvl", description="The Current level of the enemy."),
        affinity: int = nextcord.SlashOption(name="base-affinity", description="The Base Affinity of the enemy.", required=False, default=1),
    ):
        enemy = EnemyAffinity(current_level, affinity)
        enemy_affinity = human_format(enemy.calc())
        names = ["Current Level", "Base Affinity"]
        values = [current_level, affinity]
        desc = align(names, values)

        embed = nextcord.Embed(
            title="Enemy Affinity",
            description=f"Specs:\n```\n{desc}\n```\nCalculated Enemy Affinity: **{enemy_affinity}**",
            color=bot_basic_color,
        )
        await interaction.send(embed=embed)

def setup(bot):
    bot.add_cog(Warframe(bot))
