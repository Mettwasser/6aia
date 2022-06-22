import asyncio, nextcord, aiohttp
from main import bot_basic_color

links = [
    "https://api.warframestat.us/pc/cambionCycle",
    "https://api.warframestat.us/pc/cetusCycle",
    "https://api.warframestat.us/pc/vallisCycle",
]


async def get_req(url: str, session: aiohttp.ClientSession):
    async with session.get(url, headers={"language": "en"}) as response:
        return await response.json()


async def cycles():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for link in links:
            task = asyncio.create_task(get_req(link, session))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)

        embed = nextcord.Embed(
            title="Worldstates",
            description="",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        for c, data in enumerate(responses):
            if c == 0:
                obtainable = "Fass" if data["active"] == "vome" else "Vome"
                embed.description = f"**Cambion Drift**\nActive: {data['active'].capitalize()}\nTime left: {data['timeLeft']}\n\nObtainable residue: {obtainable}"

            elif c == 1:
                embed.description += (
                    f"\n\n\n**Plains of Eidolon (PoE)**\n{data['shortString']}"
                )

            elif c == 2:
                embed.description += f"\n\n\n**Orb Vallis**\n{data['shortString']}"

        embed.set_thumbnail(
            "http://n9e5v4d8.ssl.hwcdn.net/uploads/dab77b032bfa299ad8e5807e8d989544.jpg"
        )
        return embed
