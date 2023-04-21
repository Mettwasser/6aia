import nextcord
import aiohttp

from main import bot_basic_color


class Baro:
    url = "https://api.warframestat.us/pc/voidTrader/?language=en"

    @staticmethod
    async def get_current() -> nextcord.Embed:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                Baro.url,
                headers={"language": "en"},
            ) as resp:
                if resp.status != 200:
                    embed = nextcord.Embed(
                        title="Error",
                        description="Something went wrong while fetching the data! This is most likely an API error.",
                        color=bot_basic_color,
                    )
                    return embed
                json_content = await resp.json()

        inventory = json_content["inventory"]

        if not inventory:
            embed = nextcord.Embed(
                title="Baro is not here yet!",
                description=f"**Time until Baro arrives at {json_content['location']}**\n{json_content['startString']}",
                color=bot_basic_color,
            )
            return embed

        embed = nextcord.Embed(
            title="Baro's Inventory",
            description="",
            color=bot_basic_color,
            timestamp=nextcord.utils.utcnow(),
        )
        for item in inventory:
            embed.add_field(
                name=item["item"],
                value=f"<:ducats:885579733939667024> {item['ducats']}\n<:credits:885576185034194954> {item['credits']}",
            )
        embed.set_thumbnail(
            url="https://static.wikia.nocookie.net/warframe/images/a/a7/TennoCon2020BaroCropped.png/revision/latest/scale-to-width-down/350?cb=20200712232455"
        )
        embed.url = "https://warframe.fandom.com/wiki/Baro_Ki%27Teer"
        return embed