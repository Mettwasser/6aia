import nextcord, aiohttp
from main import bot_basic_color

class Invasion:
    url = "https://api.warframestat.us/pc/invasions/?language=en"


    @staticmethod
    async def get_current():
        async with aiohttp.ClientSession() as session:
            async with session.get(
                Invasion.url,
                headers={"language": "en"},
            ) as resp:
                if resp.status != 200:
                    return nextcord.Embed(
                        title="Error",
                        description="An error occured. This is probably due to an API error.",
                        color=bot_basic_color,
                    )

                r = await resp.json()
                embed = nextcord.Embed(
                    title="Current Invasions", description="", color=bot_basic_color
                )
                for c, invasion in enumerate(r, 1):
                    embed.description += f"""
    **Invasion #{c}**
    Node: {invasion["node"]}
    Attacker: {invasion["attacker"]["faction"]} | Reward: {invasion["attacker"]["reward"]["asString"]}
    Defender: {invasion["defender"]["faction"]} | Reward: {invasion["defender"]["reward"]["asString"]}\n
    """

        return embed
