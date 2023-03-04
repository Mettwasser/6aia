import nextcord, aiohttp
from main import bot_basic_color

class Worldstates:

    @staticmethod
    async def get_all() -> nextcord.Embed:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.warframestat.us/pc/?language=en", headers={"language": "en"}) as response:
                r = await response.json()

        embed = nextcord.Embed(
            title="Worldstates",
            description="",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )

        obtainable = "Fass" if r["cambionCycle"]["active"] == "vome" else "Vome"
        embed.description = f"**Cambion Drift**\nActive: {r['cambionCycle']['active'].capitalize()}\nTime left: {r['cambionCycle']['timeLeft']}\n\nObtainable residue: {obtainable}"

        embed.description += (
            f"\n\n\n**Plains of Eidolon (PoE)**\n{r['cetusCycle']['shortString']}"
        )

        embed.description += f"\n\n\n**Orb Vallis**\n{r['vallisCycle']['shortString']}"

        embed.set_thumbnail(
            "http://n9e5v4d8.ssl.hwcdn.net/uploads/dab77b032bfa299ad8e5807e8d989544.jpg"
        )
        return embed
