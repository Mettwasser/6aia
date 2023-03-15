from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from WFMCache import WFMCache

from other.wf.utils import check_mod_rank, WFMHOST



class ItemAverage:
    def __init__(self, average_prive: float, total_sales: int, moving_average: float) -> None:
        self.average_prive = average_prive
        self.total_sales = total_sales
        self.moving_average = moving_average

    @classmethod
    async def get_average(
        cls: ItemAverage,
        platform: str,
        item_url_name: str,
        normal_item_name: str,
        mod_rank: int,
        wfm_cache: WFMCache,
    ) -> ItemAverage:
        
        
        r = (await wfm_cache._request(WFMHOST + f"/items/{item_url_name}/statistics", platform=platform))["payload"]["statistics_closed"]["48hours"]

        # check if the item has a mod rnak
        await check_mod_rank(wfm_cache, item_url_name, mod_rank)


        # filter out not needed mod ranks
        sales = list(
            filter(
                lambda item: (
                    item["mod_rank"] == mod_rank if "mod_rank" in item else True
                ),
                r,
            )
        )

        if not sales:
            raise IndexError(
                f"{normal_item_name} {'(Rank {})'.format(mod_rank) if mod_rank is not None else ''} had no sales in the last 48 hours."
            )

        price_of_all = sum([item_sold["avg_price"] for item_sold in sales])
        total_sales = len(sales)

        moving_avg = None

        # try to get the moving average
        for item in sales:
            if "moving_avg" in item:
                moving_avg = item["moving_avg"]
                break


        # check if moving average was found
        if moving_avg is None:
            moving_avg = "-"


        # calculate average price
        avg_price = round((price_of_all / total_sales), 1)


        return cls(avg_price, total_sales, moving_avg)

