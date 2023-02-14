import asyncio
import nextcord

class DeferTimer:

    @staticmethod
    async def start(interaction: nextcord.Interaction, timeout: float = 2.5, do_debug: bool = False):
        await asyncio.sleep()

        if interaction.response.is_done():
            return

        if do_debug:
            print("Defered command!")

        await interaction.response.defer()