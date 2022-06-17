import aiohttp
from .utils import HOST, check_mod_rank


async def get_avg(
    platform: str,
    item_url_name: str,
    normal_item_name: str,
    mod_rank: int,
    session: aiohttp.ClientSession = None,
):
    try:
        session_created = False
        if session is None:
            session = aiohttp.ClientSession()
            session_created = True
        headers = {"Platform": platform}
        async with session.get(
            HOST + f"/items/{item_url_name}/statistics", headers=headers
        ) as resp:
            r = (await resp.json())["payload"]["statistics_closed"]["48hours"]

        await check_mod_rank(session, item_url_name, mod_rank)

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

        avg_price = round((price_of_all / total), 1)
        if session_created:
            await session.close()
        return (avg_price, total)
    except Exception as e:
        if session_created:
            await session.close()
        if isinstance(e, KeyError):
            raise KeyError(normal_item_name)  # for wl
        raise e
