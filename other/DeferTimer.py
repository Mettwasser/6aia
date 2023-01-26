import asyncio
import nextcord

class DeferTimer:
    def __init__(self, interaction: nextcord.Interaction, timeout: float = 2.5) -> None:
        self.__timeout = timeout
        self.cancel = False
        self.__interaction = interaction

        self.do_debug = False

    async def start(self):
        await asyncio.sleep(self.__timeout)

        if self.cancel:
            return

        if self.do_debug:
            print("Defered command!")

        await self.__interaction.response.defer()