import aiohttp, datetime
from main import bot_basic_color
from nextcord import Embed, utils


async def build_arbi_embed(platform: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.warframestat.us/{platform}/arbitration/?language=en",
            headers={"language": "en"},
        ) as resp:
            if resp.status != 200:
                return Embed(
                    title="Error",
                    description="An error occured. This is probably due to an API error.",
                    color=bot_basic_color,
                )
            r = await resp.json()

    utcnow = utils.utcnow()
    tz = utcnow.tzinfo
    time_left = datetime.datetime.strptime(
        r["expiry"], "%Y-%m-%dT%H:%M:%S.%fZ"
    ).replace(tzinfo=tz) - (utcnow)
    hours_left = time_left.seconds // 3600
    mins_left = (time_left.seconds // 60) % 60
    secs_left = time_left.seconds % 60
    eta = "{}{}{}s".format(
        f"{hours_left}h " if hours_left != 0 else "",
        f"{mins_left}m " if mins_left != 0 else "",
        secs_left,
    )

    embed = Embed(
        title="Current Arbitration",
        description=f"Node: {r['node']}\n\nEnemy: {r['enemy']}\n\nMission Type: {r['type']}\n\nExpires in: {eta}",
        color=bot_basic_color,
    )

    return embed
