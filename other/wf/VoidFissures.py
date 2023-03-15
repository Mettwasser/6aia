# Filters
import datetime
import aiohttp, nextcord, re
from main import bot_basic_color
from other.utils import Align
from other.wf.utils import platforms_visualized

class VoidFissures:
    url = "https://api.warframestat.us/pc/fissures/?language=en"


    @staticmethod
    def general_filter(mission):
        if (mission["expired"] is False) and (
            mission["isStorm"] is False and "Kuva" not in mission["nodeKey"]
        ):
            return True
        return False

    @staticmethod
    def is_efficient(mission: dict, revert=False) -> bool:
        if mission["expired"] or mission["isStorm"]:
            if revert:
                return True
            return False
        
        if "Kuva" in mission["nodeKey"]:
            if revert:
                return True
            return False
        
        if (
            mission["missionType"] == "Capture"
            or mission["missionType"] == "Sabotage"
            or mission["missionType"] == "Rescue"
            or mission["missionType"] == "Extermination"
            or (mission["missionType"] == "Survival" and mission["isHard"])
        ):
            return True
        return False

    @staticmethod
    async def get_current() -> nextcord.Embed:
        async with aiohttp.ClientSession() as session:
            async with session.get(VoidFissures.url, headers={"language": "en"}) as r:

                if r.status == 200:
                    rj = await r.json()
                else:
                    return None

        connectors = [None, None, None, None]

        # example: Ishtar (Venus) - only keeps the venus part
        reg_expr = r'^.*\((.*)\)$'
        # replace with the first captured group
        reg_repl = r'\1'

        should_run = [[f"{i['tier']}", f" {i['missionType']}", f"{re.sub(reg_expr, reg_repl, i['node'])}", f"{VoidFissures.__convert_time_format(i['expiry'])}", f"{'Steel Path' if i['isHard'] else 'Normal'}"] 
                      for i in sorted(filter(VoidFissures.is_efficient, rj), key=lambda x: x["tierNum"])]
        
        sorted(should_run, key=lambda item: "Steel Path" in item, reverse=True)

        shouldnt_run = [[f"{i['tier']}", f"{i['missionType']}", f"{re.sub(reg_expr, reg_repl, i['node'])}", f"{VoidFissures.__convert_time_format(i['expiry'])}", f"{'Steel Path' if i['isHard'] else 'Normal'}"] 
                         for i in sorted(filter(lambda v: not VoidFissures.is_efficient(v, revert=True), rj), key=lambda x: x["tierNum"])]

        sorted(shouldnt_run, key=lambda item: "Steel Path" in item, reverse=True)

        embed = nextcord.Embed(
            title=f"Active Fissures",
            description=f"**Fissures you SHOULD run:**\n\n```{Align.alignmany(connectors, *should_run, amount_newlines=2)}```" +
                        f"\n\n\n**Fissures you SHOULDN'T run:**```\n\n{Align.alignmany(connectors, *shouldnt_run, amount_newlines=2)}```"
            if should_run
            else f"**All Fissures**:```{Align.alignmany(connectors, *shouldnt_run, amount_newlines=2)}```",
            color=bot_basic_color,
        )
        embed.set_thumbnail(
            url="https://static.wikia.nocookie.net/warframe/images/a/ae/VoidProjectionsIronD.png/revision/latest?cb=20160709035804"
        )

        return embed

    @staticmethod
    def __convert_time_format(expiry_str: str):
        # Convert the expiry string to a datetime object
        expiry = datetime.datetime.fromisoformat(expiry_str[:-1])

        # Calculate the remaining time in seconds
        remaining = (expiry - datetime.datetime.utcnow()).total_seconds()

        # Convert the remaining time to hours with one decimal place
        remaining_hours = round(remaining / 3600, 1)

        # Format the remaining time as a string with a comma separating the integer and decimal parts
        formatted_time = '{:,.1f}h'.format(remaining_hours)

        if "-" in formatted_time:
            return "-" # expired

        return formatted_time
