import aiohttp, nextcord, datetime
from main import bot_basic_color


async def build_arbi_embed(platform: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.warframestat.us/{platform}/arbitration/",
            headers={"language": "en"},
        ) as resp:
            if resp.status != 200:
                return nextcord.Embed(
                    title="Error",
                    description="An error occured. This is probably due to an API error.",
                    color=bot_basic_color,
                )
    r = await resp.json()
    time_left = datetime.datetime.strptime(r["expiry"], "%Y-%m-%dT%H:%M:%S.%fZ") - (
        nextcord.utils.utcnow()
    )
    hours_left = time_left.seconds // 3600
    mins_left = (time_left.seconds // 60) % 60
    secs_left = time_left.seconds % 60
    eta = f"{hours_left}h {mins_left}m {secs_left}s"

    embed = nextcord.Embed(
        title="Current Arbitration",
        description=f"Node: {r['node']}\nEnemy: {r['enemy']}\nMission Type: {r['type']}\nExpires in: {eta}",
        color=bot_basic_color,
    )
