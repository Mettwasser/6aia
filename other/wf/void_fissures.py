# Filters
import aiohttp


def general_filter(mission):
    if (mission["expired"] is False) and (
        mission["isStorm"] is False and "Kuva" not in mission["nodeKey"]
    ):
        return True
    return False


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
    ):
        return True
    return False


async def vf(platform):
    link = f"https://api.warframestat.us/{platform}/fissures"
    async with aiohttp.ClientSession() as session:
        async with session.get(link, headers={"language": "en"}) as r:

            if r.status == 200:
                rj = await r.json()
            else:
                return None

    should_run = []
    for i in sorted(filter(is_efficient, rj), key=lambda x: x["tierNum"]):
        x = (
            f"{i['tier']} -"
            + f" {i['missionType']} :"
            + f" {i['node']}"
            + f" - {i['eta']}"
        )

        should_run.append(x)

    shouldnt_run = []
    for i in sorted(
        filter(lambda v: not is_efficient(v, revert=True), rj),
        key=lambda x: x["tierNum"],
    ):
        x = (
            f"{i['tier']} -"
            + f" {i['missionType']} :"
            + f" {i['node']}"
            + f" - {i['eta']}"
        )

        shouldnt_run.append(x)

    values = (
        {"should": should_run, "shouldnt": shouldnt_run}
        if should_run
        else should_run + shouldnt_run
    )
    return values
