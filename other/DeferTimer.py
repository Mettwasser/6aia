import asyncio
import nextcord

class DeferTimer:
    def __init__(self, interaction: nextcord.Interaction, timeout: float = 2.5) -> None:
        self.__timeout = timeout
        self.__interaction = interaction

        self.__do_debug = False

    async def start(self):
        await asyncio.sleep(self.__timeout)

        if self.__interaction.response.is_done():
            return

        if self.__do_debug:
            print("Defered command!")

        await self.__interaction.response.defer()