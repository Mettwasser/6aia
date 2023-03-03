import asyncio
import asqlite, nextcord, datetime
from discord import Interaction
from ..utils import disable_buttons, to_timestamp
from .utils import ModRankError, check_mod_rank, WFMHOST, platforms_visualized
from main import bot_basic_color
from nextcord.ext import application_checks
from io import StringIO
from other.WFMCache import *

DB = "wfm_wl.db"


def to_item_name(url_name: str) -> str:
    return " ".join(url_name.split("_")).title()


async def create_wl_table():
    async with asqlite.connect(DB) as con:
        async with con.cursor() as cur:
            await cur.execute(
                """
            CREATE TABLE IF NOT EXISTS wl (
                user INT,
                url_name TEXT,
                platform TEXT,
                mod_rank INT,
                is_mod TEXT,
                PRIMARY KEY (user, url_name, mod_rank)
            )
            """
            )


async def wl_is_mod(interaction: Interaction, url_name: str):
    async with asqlite.connect(DB) as con:
        async with con.cursor() as cur:
            await cur.execute(
                """
            SELECT user, url_name, is_mod FROM wl WHERE user = ? and url_name = ?
            """,
                (interaction.user.id, url_name),
            )
            res = await cur.fetchone()
            if res is None:
                return False
            return True if res["is_mod"] == "TRUE" else False


async def wl_add(
    interaction: Interaction, url_name: str, platform: str, mod_rank: int, is_mod: str
):
    async with asqlite.connect(DB) as con:
        async with con.cursor() as cur:
            await cur.execute(
                """
            INSERT INTO wl VALUES (?,?,?,?,?)
            """,
                (interaction.user.id, url_name, platform, mod_rank, is_mod),
            )


async def wl_remove(row_id: int):
    async with asqlite.connect(DB) as con:
        async with con.cursor() as cur:
            await cur.execute(
                """
            DELETE FROM wl WHERE rowid = ?
            """,
                (row_id,),
            )


async def get_wl_items(interaction: Interaction):
    async with asqlite.connect(DB) as con:
        async with con.cursor() as cur:
            await cur.execute(
            """
            SELECT rowid, * FROM wl WHERE user = ?
            """,
                (interaction.user.id),
            )
            return tuple(await cur.fetchall())


async def clear_wl_items(interaction: Interaction):
    async with asqlite.connect(DB) as con:
        async with con.cursor() as cur:
            await cur.execute(
                """
            DELETE FROM wl WHERE user = ?
            """,
                (interaction.user.id,),
            )


async def get_avg_wl(
    platform: str,
    item_url_name: str,
    normal_item_name: str,
    mod_rank: int,
    interaction: nextcord.Interaction,
    wfm_cache: WFMCache,
):
    try:
        json = (await wfm_cache._request(WFMHOST + f"/items/{item_url_name}/statistics", platform=platform))["payload"]["statistics_closed"]["48hours"]

        await check_mod_rank(wfm_cache, item_url_name, mod_rank)
        item_is_mod = await wl_is_mod(interaction, item_url_name)

        json = list(
            filter(
                lambda item: (
                    item["mod_rank"] == mod_rank if "mod_rank" in item else True
                ),
                json,
            )
        )

        if not json:
            raise IndexError(
                f"{normal_item_name} {'(Rank {})'.format(mod_rank) if mod_rank is not None else ''} had no sales in the last 48 hours."
            )

        price_of_all = 0
        total = len(json)
        for item_sold in json:
            price_of_all += item_sold["avg_price"]

        avg_price = round((price_of_all / total), 1)
        return (avg_price, total, item_url_name, item_is_mod, mod_rank)
    except Exception as e:
        if isinstance(e, KeyError):
            raise KeyError(normal_item_name)  # for wl
        raise e


async def build_embed(interaction: Interaction, wfm_cache: WFMCache):
    items = await get_wl_items(interaction)
    platform = items[0]["platform"]

    embed = nextcord.Embed(
        title=f"Average prices of your watchlist ({platforms_visualized[platform]})",
        description="",
        color=bot_basic_color,
    )

    tasks = []
    for item in items:
        tasks.append(
            asyncio.create_task(
                get_avg_wl(
                    platform,
                    item["url_name"],
                    to_item_name(item["url_name"]),
                    item["mod_rank"],
                    interaction,
                    wfm_cache=wfm_cache,
                )
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        try:
            if isinstance(result, Exception):
                raise result
            else:
                embed.description += f"**{to_item_name(result[2])}{' (Rank {})'.format(result[4]) if result[3] else ''}**\nAverage price: **{result[0]}**\n**{result[1]}**" + \
                f" sales in the last 48 hours\n{to_timestamp(datetime.datetime.fromtimestamp(wfm_cache.cache_time[platform][WFMHOST + f'/items/{result[2]}/statistics']), 'R')}\n\n"

        except KeyError as e:
            embed.description += f"Unable to find the item `({e.args[0]})`\n\n"

        except IndexError as e:
            embed.description += e.args[0] + "\n\n"

        except ModRankError as e:
            embed.description += f"The rank of this item exceeds the maximum rank.\n`Max. Rank for {e.args[1]}: {e.args[0]}`\n\n"

    return embed


async def export_as_file(interaction: Interaction, wfm_cache: WFMCache):
    embed = await build_embed(interaction, wfm_cache)
    header = (
        f"Average prices of your watchlist - {nextcord.utils.utcnow().date()}\n\n\n"
    )

    embed: nextcord.Embed
    string = embed.description.replace("**", "")
    sio = StringIO(header + string)
    file = nextcord.File(
        sio,
        filename=f"wl-{nextcord.utils.utcnow().date()}.txt",
        description=f"The prices of your watchlist {nextcord.utils.utcnow().date()}",
    )
    return file


class WLRemoveButton(nextcord.ui.Button):
    def __init__(self, warn_pos: int, rowid: int):
        super().__init__(style=nextcord.ButtonStyle.grey, label=f"{warn_pos}")
        self.rowid = rowid

    async def callback(self, interaction: nextcord.Interaction):
        await wl_remove(self.rowid)
        await self.update(interaction)

    async def update(self, interaction: nextcord.Interaction):
        # disable the button pressed, so it can't be pressed again and indicate that it was pressed by turning it red
        self.style = nextcord.ButtonStyle.red
        self.disabled = True
        self.view.removed_rowids.append(self.rowid)

        # Update the embed, to cross out removed warns
        embed = nextcord.Embed(
            description=f"Your Watchlist ({self.view.items[0]['platform']}):",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        for c, item in enumerate(self.view.items, 1):
            itemname = to_item_name(item["url_name"])
            if item["rowid"] in self.view.removed_rowids:
                embed.description += f"\n\n~~{c}. `{itemname}{' (R{})'.format(item['mod_rank']) if await wl_is_mod(interaction, item['url_name']) else ''}`~~"
            else:
                embed.description += f"\n\n{c}. `{itemname}{' (R{})'.format(item['mod_rank']) if await wl_is_mod(interaction, item['url_name']) else ''}`"

        # check if all warns were removed, if so disable everything and stop listening to the view
        if all([x["rowid"] in self.view.removed_rowids for x in self.view.items]):
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


class WLRemoveView(nextcord.ui.View):
    def __init__(
        self,
        interaction: nextcord.Interaction,  # for interaction_check
        items: list,  # list of items to be removed, is being parsed around
        *,
        timeout=45,
    ):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.items = items
        self.removed_rowids = []

        buttons = [WLRemoveButton(c + 1, item["rowid"]) for c, item in enumerate(items)]

        for button in buttons:
            self.add_item(button)
        self.add_item(CancelButton())

    async def on_timeout(self) -> None:
        disable_buttons(self)
        await self.message.edit(view=self)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user != self.interaction.user:
            raise application_checks.ApplicationMissingPermissions(
                "You haven't started this Command."
            )
        else:
            return True

    # async def on_error(
    #     self,
    #     error: Exception,
    #     item: nextcord.ui.Item,
    #     interaction: nextcord.Interaction,
    # ) -> None:
    #     if isinstance(error, application_checks.ApplicationMissingPermissions):
    #         await interaction.send(error.args[0], ephemeral=True)
    #     else:
    #         await interaction.send(
    #             f"{error}\n\nReport this to a developer.",
    #             ephemeral=True,
    #         )
