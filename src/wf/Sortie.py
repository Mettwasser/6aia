import nextcord, aiohttp
from main import bot_basic_color

class Sortie:
    url = "https://api.warframestat.us/pc/sortie/?language=en"


    @staticmethod
    async def get_current() -> nextcord.Embed:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                Sortie.url,
                headers={"language": "en"},
            ) as resp:
                if resp.status != 200:
                    return nextcord.Embed(
                        title="Error",
                        description="An error occured. This is probably due to an API error.",
                        color=bot_basic_color,
                    )

                r = await resp.json()

        missions = [
            [
                x["node"],
                x["missionType"],
                x["modifier"],
            ]
            for x in r["variants"]
        ]
        embed = nextcord.Embed(
            title="Current Sortie",
            description=f"""
    **First Mission**
Node: {missions[0][0]}
Mission Type: {missions[0][1]}
Modifier: {missions[0][2]}

**Second Mission**
Node: {missions[1][0]}
Mission Type: {missions[1][1]}
Modifier: {missions[1][2]}

**Third Mission**
Node: {missions[2][0]}
Mission Type: {missions[2][1]}
Modifier: {missions[2][2]}

**-------------------------------**

Faction: {r['faction']}
Time left: {r['eta']}
    """,
            color=bot_basic_color,
        )
        return embed
