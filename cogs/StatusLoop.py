import nextcord, asyncio, aiohttp
from nextcord.ext import commands, tasks


class StatusLoop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.barocheck.start()

    @tasks.loop(minutes=15)
    async def barocheck(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.warframestat.us/pc/voidTrader", headers={"language": "en"}
            ) as resp:
                if resp.status != 200:
                    return
                json_content = await resp.json()

        if json_content["active"]:
            await self.bot.change_presence(
                activity=nextcord.Game(name=f"Baro is here! - /wf baro || /help")
            )

        else:
            await self.bot.change_presence(
                activity=nextcord.Game(
                    name=f"with {sum(1 for _ in self.bot.get_all_members())} users | /help"
                )
            )

    @barocheck.before_loop
    async def before_barocheck(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(StatusLoop(bot))
