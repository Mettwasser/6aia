from typing import Iterable
import nextcord


async def autocomplete_response(
    cog=None, interaction: nextcord.Interaction = None, kwarg: str = None
):
    if not kwarg:
        # send the full autocomplete list
        await interaction.response.send_autocomplete(list())
        return
    # send a list of nearest matches from the list of dog breeds
    autocompletes = [item for item in list() if item.lower().startswith(kwarg.lower())]
    await interaction.response.send_autocomplete(autocompletes)
