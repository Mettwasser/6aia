from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from WFMCache import WFMCache

import nextcord
from main import bot_basic_color

from typing import Iterable
from datetime import datetime
import enum

from other.wf.utils import WFMHOST

from other.wf.Errors import ModRankError, ItemNotFound
from other.wf.utils import is_mod, platforms_visualized_wfm
from other.wf.wfm_watchlist import to_item_name

from other.utils import disable_buttons    

class SearchErrorCommandType(enum.Enum):
    # whether the error occured in the average or search command
    Search = 1
    Average = 2

class SearchError(Exception):
    def __init__(
            self,
            error, 
            wfm_cache: WFMCache,
            url_name: str,
            search_filter: str,
            mod_rank: int,
            platform: str,
            cmd_type: SearchErrorCommandType,
            *args: object
        ) -> None:
        super().__init__(*args)
        self.wfm_cache = wfm_cache
        self.url_name = url_name
        self.actual_name = to_item_name(url_name)
        self.original_error = error
        self.search_filter = search_filter
        self.mod_rank = mod_rank
        self.platform = platform
        self.command_type = cmd_type

class WFMSearch:

    # SEARCHMANY
    class JumpToPage(nextcord.ui.Modal):
        def __init__(self, max_pages: int):
            super().__init__(title="Jump to Page", timeout=30)
            self.valid = False

            self.number = nextcord.ui.TextInput(
                label="The page you want to jump to",
                min_length=1,
                max_length=len(str(max_pages)),
            )
            self.add_item(self.number)
            self.pages = max_pages
            self.timeout_triggered = False

        async def callback(self, interaction: nextcord.Interaction):
            user_input = int(self.number.value)
            if user_input in range(1, self.pages + 1):
                self.valid = True
                self.page = user_input
            self.stop()

        async def on_timeout(self) -> None:
            self.timeout_triggered = True


    class WFBrowser(nextcord.ui.View):
        def __init__(
            self,
            json_content: Iterable,
            amount_of_orders: int,
            item_name: str,
            url_name: str,
            initial_interaction: nextcord.Interaction,
            search_filter: str,
            mod_rank: int,
            wfm_cache: WFMCache,
            platform: str,
            *,
            timeout=45,
        ):
            super().__init__(timeout=timeout)

            self.json_content = json_content

            orders = sorted(
                list(
                    filter(
                        lambda item: (
                            item["user"]["status"] == search_filter
                            or search_filter == "all"
                        )
                        and item["order_type"] == "sell"
                        and (item["mod_rank"] == mod_rank if "mod_rank" in item else True),
                        json_content["payload"]["orders"],
                    )
                ),
                key=lambda x: x["platinum"],
            )

            self.orders = orders[0:amount_of_orders]
            self.max_orders = len(self.orders)
            self.current = 0
            self.item_name = item_name
            self.cached_embeds: dict[int : nextcord.Embed] = {}
            self.first = True
            self.page = 1
            self.url_name = url_name
            self.initial_interaction = initial_interaction
            self.wfm_cache = wfm_cache
            self.platform = platform

        async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
            return self.initial_interaction.user == interaction.user

        async def on_timeout(self) -> None:
            disable_buttons(self)
            await self.msg.edit(view=self)

        def create_embed(self):
            self.children[2].label = f"{self.page}/{self.max_orders}"
            if not self.current in self.cached_embeds:
                current_order = self.orders[self.current]

                plat_cost = current_order["platinum"]
                order_type = current_order["order_type"].capitalize()
                quantity = current_order["quantity"]

                user_info = current_order["user"]

                user_rep = user_info["reputation"]
                if user_info["avatar"] == None:
                    user_avatar = (
                        "https://warframe.market/static/assets/user/default-avatar.png"
                    )
                else:
                    user_avatar = "https://warframe.market/static/assets/{}".format(
                        user_info["avatar"]
                    )
                user_name = user_info["ingame_name"]
                status = user_info["status"].capitalize()
                creation_date = datetime.fromisoformat(current_order["creation_date"])
                creation_date_ts = creation_date.timestamp()

                include = self.json_content["include"]["item"]["items_in_set"]

                icon_url = "https://warframe.market/static/assets/{}".format(
                    include[0]["icon"]
                )
                wiki_link = include[0]["en"]["wiki_link"]

                embed = nextcord.Embed(color=bot_basic_color)
                embed.title = (
                    f"Offer #{self.page} for {to_item_name(self.url_name)}".format(
                        str(self.item_name)
                    )
                )
                embed.url = f"https://warframe.market/items/{self.url_name}"
                embed.add_field(name="Order Type", value="{}".format(order_type))
                embed.add_field(name="Price", value="{}p".format(plat_cost))
                embed.add_field(name="Quantity", value="{}".format(quantity))
                embed.add_field(
                    name="Creation Date", value="<t:{}:D>".format(int(creation_date_ts))
                )
                if current_order.get("mod_rank") is not None:
                    embed.add_field(name="Rank", value=current_order["mod_rank"])
                    embed.add_field(
                        name="Buy",
                        value="`/w {} Hi! I want to buy: {} (rank {}) for {} platinum. (warframe.market)`".format(
                            user_name,
                            self.item_name,
                            current_order["mod_rank"],
                            plat_cost,
                        ),
                        inline=True,
                    )
                else:
                    embed.add_field(
                        name="Buy",
                        value="`/w {} Hi! I want to buy: {} for {} platinum. (warframe.market)`".format(
                            user_name, self.item_name, plat_cost
                        ),
                        inline=True,
                    )
                    pass

                embed.add_field(
                    name="{}'s Reputation".format(user_name),
                    value="{}".format(user_rep),
                    inline=False,
                )
                embed.add_field(name="Status", value=status, inline=False)
                embed.add_field(
                    name="{}'s WFM Profile".format(user_name),
                    value="[Profile](https://warframe.market/profile/{})".format(user_name),
                    inline=False,
                )
                embed.add_field(
                    name="Wiki", value="[Click Here]({})".format(wiki_link), inline=False
                )

                embed.set_author(name="{}".format(user_name), icon_url=user_avatar)
                embed.set_thumbnail(url=icon_url)

                embed.set_footer(text=f"Last cached", icon_url="https://image.winudf.com/v2/image/bWFya2V0LndhcmZyYW1lX2ljb25fMTUzODM1NjAxOV8wMjI/icon.png?w=&fakeurl=1")
                embed.timestamp = datetime.fromtimestamp(self.wfm_cache.cache_time[self.platform][WFMHOST + f'/items/{self.url_name}/orders'])
                self.cached_embeds[self.current] = embed
                return embed

            else:
                return self.cached_embeds[self.current]

        def check(self):
            if self.current == self.max_orders - 1 or self.current == self.max_orders - 1:
                d = True
            else:
                d = False
            for child in self.children[3:5]:
                child.disabled = d

            if self.current == 0:
                d = True
            else:
                d = False
            for child in self.children[0:2]:
                child.disabled = d

        async def update_embed(self):
            embed = self.create_embed()

            if self.first:
                for child in self.children[0:2]:
                    child.disabled = False
                self.first = False

            self.check()

            await self.msg.edit(view=self, embed=embed)

        @nextcord.ui.button(emoji="⏪", style=nextcord.ButtonStyle.blurple, disabled=True)
        async def on_rewind(
            self, button: nextcord.Button, interaction: nextcord.Interaction
        ):
            self.current = 0
            self.page = 1
            await self.update_embed()

        @nextcord.ui.button(emoji="◀️", style=nextcord.ButtonStyle.green, disabled=True)
        async def on_back(self, button: nextcord.Button, interaction: nextcord.Interaction):
            self.current -= 1
            self.page -= 1

            await self.update_embed()

        @nextcord.ui.button(label=f"X", style=nextcord.ButtonStyle.grey, disabled=True)
        async def display(self, button: nextcord.Button, interaction: nextcord.Interaction):
            pass

        @nextcord.ui.button(emoji="▶️", style=nextcord.ButtonStyle.green)
        async def on_forward(
            self, button: nextcord.Button, interaction: nextcord.Interaction
        ):

            self.current += 1
            self.page += 1

            await self.update_embed()

        @nextcord.ui.button(emoji="⏩", style=nextcord.ButtonStyle.blurple)
        async def on_fast_forward(
            self, button: nextcord.Button, interaction: nextcord.Interaction
        ):

            self.current = self.max_orders - 1
            self.page = self.max_orders
            await self.update_embed()

        @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red, row=2)
        async def on_cancel(
            self, button: nextcord.Button, interaction: nextcord.Interaction
        ):
            disable_buttons(self)
            await interaction.response.edit_message(view=self)

            self.stop()

        @nextcord.ui.button(label="Jump to page", style=nextcord.ButtonStyle.blurple, row=2)
        async def on_jump_to(
            self, button: nextcord.Button, interaction: nextcord.Interaction
        ):
            modal = WFMSearch.JumpToPage(self.max_orders)
            await interaction.response.send_modal(modal)
            await modal.wait()
            if hasattr(modal, "page"):
                self.current = modal.page - 1
                self.page = modal.page
                await self.update_embed()

            elif modal.timeout_triggered:
                await interaction.send(
                    "You didn't enter anything -> Interaction cancelled.", ephemeral=True
                )
            else:
                await interaction.send(
                    f"{modal.number.value} is not a valid Page!", ephemeral=True
                )


    # SINGLE SEARCH

    @staticmethod
    def single(
        search_filter: str, mod_rank: int, json_content: dict, url_name: str, wfm_cache: WFMCache, platform: str
    ) -> nextcord.Embed:
        filtered_wfm = list(
            filter(
                lambda item: (
                    item["user"]["status"] == search_filter or search_filter == "all"
                )
                and item["order_type"] == "sell"
                and (item["mod_rank"] == mod_rank if "mod_rank" in item else True),
                json_content["payload"]["orders"],
            )
        )
        sorted_wfm = sorted(filtered_wfm, key=lambda x: x["platinum"])
        first_wfm_order = sorted_wfm[0]

        plat_cost = first_wfm_order["platinum"]
        order_type = first_wfm_order["order_type"].capitalize()
        quantity = first_wfm_order["quantity"]

        user_info = first_wfm_order["user"]

        user_rep = user_info["reputation"]
        if user_info["avatar"] == None:
            user_avatar = "https://warframe.market/static/assets/user/default-avatar.png"
        else:
            user_avatar = "https://warframe.market/static/assets/{}".format(
                user_info["avatar"]
            )
        user_name = user_info["ingame_name"]
        status = user_info["status"].capitalize()
        creation_date = datetime.fromisoformat(first_wfm_order["creation_date"])
        creation_date_ts = creation_date.timestamp()

        include = json_content["include"]["item"]["items_in_set"]

        icon_url = "https://warframe.market/static/assets/{}".format(include[0]["icon"])
        wiki_link = include[0]["en"]["wiki_link"]

        embed = nextcord.Embed(color=bot_basic_color)
        embed.title = "Cheapest offer for {} on warframe.market".format(
            to_item_name(url_name)
        )
        embed.add_field(name="Order Type", value="{}".format(order_type))
        embed.add_field(name="Price", value="{}p".format(plat_cost))
        embed.add_field(name="Quantity", value="{}".format(quantity))
        embed.add_field(
            name="Creation Date", value="<t:{}:D>".format(int(creation_date_ts))
        )
        if first_wfm_order.get("mod_rank") is not None:
            embed.add_field(name="Mod Rank", value=first_wfm_order["mod_rank"])
            embed.add_field(
                name="Buy",
                value="`/w {} Hi! I want to buy: {} (rank {}) for {} platinum. (warframe.market)`".format(
                    user_name,
                    url_name,
                    first_wfm_order["mod_rank"],
                    plat_cost,
                ),
                inline=True,
            )
        else:
            embed.add_field(
                name="Buy",
                value="`/w {} Hi! I want to buy: {} for {} platinum. (warframe.market)`".format(
                    user_name, url_name, plat_cost
                ),
                inline=True,
            )
            pass

        embed.add_field(
            name="{}'s Reputation".format(user_name),
            value="{}".format(user_rep),
            inline=False,
        )
        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(
            name="{}'s WFM Profile".format(user_name),
            value="[Profile](https://warframe.market/profile/{})".format(user_name),
            inline=False,
        )
        embed.add_field(
            name="Wiki",
            value="[Click Here]({})".format(wiki_link),
            inline=False,
        )

        embed.set_author(name="{}".format(user_name), icon_url=user_avatar)
        embed.set_thumbnail(url=icon_url)

        embed.set_footer(text=f"Last cached", icon_url="https://image.winudf.com/v2/image/bWFya2V0LndhcmZyYW1lX2ljb25fMTUzODM1NjAxOV8wMjI/icon.png?w=&fakeurl=1")
        embed.timestamp = datetime.fromtimestamp(wfm_cache.cache_time[platform][WFMHOST + f'/items/{url_name}/orders'])
        return embed

    @staticmethod
    async def handle_search_error(interaction: nextcord.Interaction, search_error: SearchError):

        error = search_error.original_error

        if isinstance(error, KeyError) or isinstance(error, ItemNotFound) or isinstance(error, AttributeError):
            title = "Invalid Item"
            desc = f"I was unable to find the item `{search_error.actual_name}` you were trying to search. Please make sure to have the correct **spelling** of the item you want to search up."


        elif isinstance(error, IndexError):
            if search_error.command_type is SearchErrorCommandType.Search:
                title = "No Offers"
                desc = f"{search_error.actual_name} has no listings! (filter: {search_error.search_filter}{', rank: {}'. format(search_error.mod_rank) if await is_mod(search_error.url_name, search_error.wfm_cache) else ''})"
            else: # SearchErrorCommandType.Average
                title = "No Sales"
                desc = f"{search_error.actual_name} had no sales in the last 48 hours! (filter: {search_error.search_filter}{', rank: {}'. format(search_error.mod_rank) if await is_mod(search_error.url_name, search_error.wfm_cache) else ''})"

        elif isinstance(error, ModRankError):
            title = "Invalid Mod Rank"
            desc  = f"The rank you entered is higher than the maximum rank of this item.\n`Max. Rank for {search_error.actual_name}: {error.args[0]}`"

        
        else:
            title = "Unexpected Error"
            desc = f"```Ignoring exception in command {interaction.application_command}\n{type(error)} {error} {error.__traceback__}```\nReport to dev.",


        title += f" ({platforms_visualized_wfm[search_error.platform]})"
        await interaction.send(embed=nextcord.Embed(title=title, description=desc, color=bot_basic_color))
