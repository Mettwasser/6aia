from main import bot_basic_color

import nextcord
import aiohttp
import asyncio
import sqlite3

from other.utils import align
from other.WFMCache import *
from other.DeferTimer import DeferTimer
from other.wf import *
from other.wf.utils import platforms_visualized

from nextcord.ext import commands

# Item list for "autocompletion"
WFMHOST = "https://api.warframe.market/v1"



class Warframe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wfm_cache: WFMCache = WFMCache()


    #################################################################################
    #                               BASE WF COMMAND                                 #
    #################################################################################


    @nextcord.slash_command(description="Warframe Command Prefix", name="wf")
    async def wf(self, interaction: nextcord.Interaction):
        # pass, this is just the command prefix, so we don't need to do anything
        pass




    #################################################################################
    #                            Warframe.Market related                            #
    #################################################################################

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

        asyncio.create_task(DeferTimer.start(interaction))
        params={"include": "item"}
        json_content = await self.wfm_cache._request(f"https://api.warframe.market/v1/items/{url_name.lower()}/orders", platform=platform, params=params)

        try:
            await check_mod_rank(self.wfm_cache, url_name, mod_rank)
            embed = WFMSearch.single(
                search_filter,
                mod_rank,
                json_content,
                url_name,
                self.wfm_cache,
                platform
            )
            await interaction.send(content=None, embed=embed)

        except Exception as e:
            raise SearchError(e, self.wfm_cache, url_name, search_filter, mod_rank)

    @search.error
    async def on_search_error(interaction: nextcord.Interaction, error):
        WFMSearch.handle_search_error(interaction, error)

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
        try:
            url_name = set_item_urlname(actual_name)

            asyncio.create_task(DeferTimer.start(interaction))

            params = {"include": "item"}
            json_content = await self.wfm_cache._request(f"https://api.warframe.market/v1/items/{url_name.lower()}/orders", platform=platform, params=params)

            await check_mod_rank(self.wfm_cache, url_name, mod_rank)

            view = WFMSearch.WFBrowser(
                json_content,
                amount_to_look_up,
                actual_name,
                url_name,
                interaction,
                search_filter,
                mod_rank,
                self.wfm_cache,
                platform
            )

            try:
                initial_embed = (
                    view.create_embed()
                    if view.max_orders > 1
                    else WFMSearch.single(
                        search_filter,
                        mod_rank,
                        json_content,
                        url_name,
                        self.wfm_cache,
                        platform
                    )
                )
            except IndexError as e:
                raise e
            if view.max_orders > 1:
                view.msg = await interaction.send(embed=initial_embed, view=view)
            else:
                await interaction.send(embed=initial_embed)

        except Exception as e:
            raise SearchError(e, self.wfm_cache, url_name, search_filter, mod_rank)

    @searchmany.error
    async def on_searchmany_error(interaction: nextcord.Interaction, error):
        WFMSearch.handle_search_error(interaction, error)

    # Gets the Average price for an Item
    @market.subcommand(
        description="Gives you the average price of an item on warframe.market."
    )
    async def average(
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
            asyncio.create_task(DeferTimer.start(interaction))
            item_is_mod = await is_mod(url_name, self.wfm_cache)

            itemavg = await get_average(
                platform, url_name, actual_name, mod_rank, self.wfm_cache
            )

            embed = nextcord.Embed(color=bot_basic_color)
            embed.title = f"Average price of {to_item_name(url_name)} {'(R{})'.format(mod_rank) if item_is_mod else ''}"
            embed.description = f"Average price: **{itemavg.average_prive}**\n**{itemavg.total_sales}** sales in the last 48 hours\nMoving average: **{itemavg.moving_average}**"
            embed.set_footer(text=f"Last cached", icon_url="https://image.winudf.com/v2/image/bWFya2V0LndhcmZyYW1lX2ljb25fMTUzODM1NjAxOV8wMjI/icon.png?w=&fakeurl=1")
            embed.timestamp = datetime.datetime.fromtimestamp(self.wfm_cache.cache_time[platform][WFMHOST + f'/items/{url_name}/statistics'])
            await interaction.send(embed=embed)

        except Exception as e:
            raise SearchError(e, self.wfm_cache, url_name, None, mod_rank)

    @average.error
    async def on_average_error(interaction: nextcord.Interaction, error):
        WFMSearch.handle_search_error(interaction, error)














    #################################################################################
    #                               WATCHLIST COMMANDS                              #
    #################################################################################




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
            await check_mod_rank(self.wfm_cache, url_name, mod_rank)
            item_is_mod = await is_mod(url_name, self.wfm_cache)


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

        except sqlite3.IntegrityError:
            return await interaction.send(
                f"Failed to add the item: `{actual_name}{' ({})'.format(mod_rank) if item_is_mod else ''}` because it is already added."
            )
        except Exception as e:
            raise SearchError(e, self.wfm_cache, url_name, None, mod_rank)

    @_wl_add.error
    async def on_average_error(interaction: nextcord.Interaction, error):
        WFMSearch.handle_search_error(interaction, error)

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
            title=f"Your Watchlist ({platforms_visualized[items[0]['platform']]}):",
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
        asyncio.create_task(DeferTimer.start(interaction, timeout = 2.0))
        items = await get_wl_items(interaction)
        if not items:
            embed = nextcord.Embed(
                description=f"Your Watchlist is Empty!",
                color=bot_basic_color,
                timestamp=nextcord.utils.utcnow(),
            )
            return await interaction.send(embed=embed)
        embed = await build_embed(interaction, self.wfm_cache)
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
            title=f"Your Watchlist ({platforms_visualized[items[0]['platform']]})",
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

        file = await export_as_file(interaction, self.wfm_cache)
        await interaction.send(file=file)



    #################################################################################
    #                             GENERAL WF COMMANDS                               #
    #################################################################################



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
        active = await VoidFissures.get_current(platform)
        efficient = active["should"] if isinstance(active, dict) else None
        inefficient = active["shouldnt"] if isinstance(active, dict) else active

        embed = nextcord.Embed(
            title=f"Active Fissures ({platform})",
            description="**Fissures you SHOULD run:**\n\n{}\n\n\n**Fissures you SHOULDN'T run:**\n\n{}".format(
                "\n\n".join(efficient), "\n\n".join(inefficient)
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
                f"https://api.warframestat.us/{platform}/voidTrader/?language=en",
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
        name="arbitration", description="Shows you the current Arbitration. (Unstable)"
    )
    async def arbitration(
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
        embed: nextcord.Embed = await Arbitration.get_current(platform)
        await interaction.send(embed=embed)

    @arbitration.error
    async def on_arbitration_error(interaction: nextcord.Interaction, error):
        if isinstance(error, APIError):
            await interaction.send(embed=nextcord.Embed(
                title="Error",
                description="An error occured. This is probably due to an API error.",
                color=bot_basic_color,
                )
            )
        else:
            raise error













    #################################################################################
    #                             CALCULATION COMMANDS                              #
    #################################################################################



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
