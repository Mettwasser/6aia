import aiohttp
from .utils import HOST, check_mod_rank
from ..WFMCache import *


async def get_avg(
    platform: str,
    item_url_name: str,
    normal_item_name: str,
    mod_rank: int,
    wfm_cache: WFMCache,
):
    try:
        r = (await wfm_cache._request(HOST + f"/items/{item_url_name}/statistics", platform=platform))["payload"]["statistics_closed"]["48hours"]

        await check_mod_rank(wfm_cache, item_url_name, mod_rank)

        r = list(
            filter(
                lambda item: (
                    item["mod_rank"] == mod_rank if "mod_rank" in item else True
                ),
                r,
            )
        )

        if not r:
            raise IndexError(
                f"{normal_item_name} {'(Rank {})'.format(mod_rank) if mod_rank is not None else ''} had no sales in the last 48 hours."
            )

        price_of_all = 0
        total = len(r)
        for item_sold in r:
            price_of_all += item_sold["avg_price"]

        for x in r:
            try:
                moving_avg = x["moving_avg"]
                break
            except KeyError:
                continue

        if "moving_avg" not in locals():
            moving_avg = "-"

        avg_price = round((price_of_all / total), 1)
        return (avg_price, total, moving_avg)
    except Exception as e:
        if isinstance(e, KeyError):
            raise KeyError(normal_item_name)  # for wl
        raise e
