from .errors import ModRankError
from ..WFMCache import *

HOST = "https://api.warframe.market/v1"


# Checks the mod Rank
async def check_mod_rank(wfm_cache: WFMCache, url_name: str, mod_rank: int):
    json_content = await wfm_cache._request(HOST + f"/items/{url_name}")

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
    json_content = await wfm_cache._request(HOST + f"/items/{url_name}")
    return "mod_max_rank" in json_content["payload"]["item"]["items_in_set"][0]


platforms_visualized = {
    "ps4": "PlayStation",
    "xb1": "Xbox",
    "pc": "PC",
    "swi": "Switch",
}