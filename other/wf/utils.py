import aiohttp
from .errors import ModRankError


HOST = "https://api.warframe.market/v1"


# Checks the mod Rank
async def check_mod_rank(session: aiohttp.ClientSession, url_name: str, mod_rank: int):
    async with session.get(HOST + f"/items/{url_name}") as resp:
        json_content = await resp.json()

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
    session: aiohttp.ClientSession = None,
    close_session_on_error: bool = True,
):
    try:
        session_created = False
        if session is None:
            session = aiohttp.ClientSession()
            session_created = True

        async with session.get(HOST + f"/items/{url_name}") as resp:
            json_content = await resp.json()

        if session_created:
            await session.close()

        return "mod_max_rank" in json_content["payload"]["item"]["items_in_set"][0]
    except Exception as e:
        if close_session_on_error:
            await session.close()
        raise e
