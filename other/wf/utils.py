import difflib
import requests
import nextcord

from cogs.Warframe import WFMHOST

from .errors import ModRankError
from ..WFMCache import *

item_dict: dict = requests.get(WFMHOST + "/items").json()["payload"]["items"]
item_names = [x["item_name"] for x in item_dict]


# Checks the mod Rank
async def check_mod_rank(wfm_cache: WFMCache, url_name: str, mod_rank: int):
    json_content = await wfm_cache._request(WFMHOST + f"/items/{url_name}")

    if "mod_max_rank" in json_content["payload"]["item"]["items_in_set"][0]:

        mod_max_rank = json_content["payload"]["item"]["items_in_set"][0][
            "mod_max_rank"
        ]
        if mod_rank > mod_max_rank:
            raise ModRankError(
                mod_max_rank, url_name
            )  # url_name is raised with it for the watchlist


async def is_mod(
    url_name: str,
    wfm_cache: WFMCache,
):
    json_content = await wfm_cache._request(WFMHOST + f"/items/{url_name}")
    return "mod_max_rank" in json_content["payload"]["item"]["items_in_set"][0]


platforms_visualized = {
    "ps4": "PlayStation",
    "xb1": "Xbox",
    "pc": "PC",
    "swi": "Switch",
}


def set_item_urlname(item_name: str):

    name = difflib.get_close_matches(
        item_name.capitalize(), [x["url_name"] for x in item_dict]
    )
    if name:
        return name[0].lower()
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