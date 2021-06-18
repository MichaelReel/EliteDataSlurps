from bisect import insort_left, insort_right
from typing import Optional
from summary.model import Commodity as StockCommodity, CostSnapshot, StockSummary
from eddn.model import (
    Commodity as EddnCommodity, 
    CommodityV3 as EddnCommodityV3,
    Message
)


class Adapter:
    __max_best = 1

    def __init__(self, target: StockSummary) -> None:
        self.stock_summary = target
        self.commodity_index = {}
        self._create_commodity_index()


    def _create_commodity_index(self) -> None:
        """
        The commodity_index is only used for lookup while the stock_summary
        is live in this adapter. We drop and re-create on file load.
        """
        for commodity in self.stock_summary.commodities:
            self.commodity_index[commodity.name] = commodity


    def _get_stock_commodity(self, name: str) -> Optional[StockCommodity]:
        if name in self.commodity_index:
            return self.commodity_index[name]
        else:
            stock_commodity = StockCommodity(name=name, best_buys=[], best_sales=[])
            self.stock_summary.commodities.append(stock_commodity)
            self.commodity_index[name] = stock_commodity
            return stock_commodity

    
    def update(self, commodity_v3: EddnCommodityV3) -> None:
        for eddn_commodity in commodity_v3.message.commodities:
            self._update_commodity_summary(eddn_commodity, commodity_v3.message)


    def _update_commodity_summary(self, eddn_commodity: EddnCommodity, message: Message):
        stock_commodity: StockCommodity = self._get_stock_commodity(eddn_commodity.name)
        cost_snapshot = CostSnapshot(
            system_name=message.system_name,
            station_name=message.station_name,
            timestamp=message.timestamp,
            buy_price=eddn_commodity.buy_price,
            stock=eddn_commodity.stock,
            sell_price=eddn_commodity.sell_price,
            demand=eddn_commodity.demand
        )
        self._insert_buy(stock_commodity, cost_snapshot)
        self._insert_sell(stock_commodity, cost_snapshot)
    

    def _insert_buy(self, stock_commodity: StockCommodity, cost_snapshot: CostSnapshot):
        if cost_snapshot.buy_price == 0:
            return
        # Put lowest prices first
        i = 0
        while i < len(stock_commodity.best_buys):
            if cost_snapshot.buy_price < stock_commodity.best_buys[i].buy_price:
                break
            i += 1
        stock_commodity.best_buys.insert(i, cost_snapshot)
        # Trim excess results
        stock_commodity.best_buys = stock_commodity.best_buys[:self.__max_best]

    def _insert_sell(self, stock_commodity: StockCommodity, cost_snapshot: CostSnapshot):
        if cost_snapshot.sell_price == 0:
            return
        # Put highest prices first
        i = 0
        while i < len(stock_commodity.best_sales):
            if cost_snapshot.sell_price > stock_commodity.best_sales[i].sell_price:
                break
            i += 1
        stock_commodity.best_sales.insert(i, cost_snapshot)
        # Trim excess results
        stock_commodity.best_sales = stock_commodity.best_sales[:self.__max_best]