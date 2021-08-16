import numpy

from typing import Optional

from config.model import StockConfig
from eddn.commodity_v3.model import (
    Commodity as EddnCommodity,
    CommodityV3 as EddnCommodityV3,
    Message,
)
from summary.dock_handler.journal_v1 import DockHandler
from summary.model import Commodity as StockCommodity, CostSnapshot, StockSummary


class StockHandler:
    def __init__(
        self, config: StockConfig, target: StockSummary, dock_handler: DockHandler
    ) -> None:
        self.config = config
        self._origin = numpy.array(self.config.origin_coords)
        self.stock_summary = target
        self.dock_handler = dock_handler
        self.commodity_index = {}
        self._create_commodity_index()
        self.save_counter = self.config.autosave_wait

    def _create_commodity_index(self) -> None:
        """
        The commodity_index is only used for lookup while the stock_summary
        is live in this adapter. We drop and re-create on file load.
        """
        for commodity in self.stock_summary.commodities:
            self.commodity_index[commodity.name.lower()] = commodity

    def _get_stock_commodity(self, name: str) -> Optional[StockCommodity]:
        if name.lower() in self.commodity_index:
            return self.commodity_index[name.lower()]
        else:
            stock_commodity = StockCommodity(name=name, best_buys=[], best_sales=[])
            self.stock_summary.commodities.append(stock_commodity)
            self.commodity_index[name.lower()] = stock_commodity
            return stock_commodity

    def update(self, commodity_v3: EddnCommodityV3) -> bool:
        """Updates the summary and returns true if it's time to save"""
        for eddn_commodity in commodity_v3.message.commodities:
            self._update_commodity_summary(eddn_commodity, commodity_v3.message)

        if self.save_counter <= 0:
            self.save_counter = self.config.autosave_wait
            return True
        else:
            self.save_counter -= 1
            return False

    def _update_commodity_summary(
        self, eddn_commodity: EddnCommodity, message: Message
    ):
        stock_commodity: StockCommodity = self._get_stock_commodity(eddn_commodity.name)
        system = message.system_name
        station = message.station_name
        if journal_dock := self.dock_handler.get_dock_entry(
            system=system, station=station
        ):
            station_type = journal_dock.station_type
            coords = numpy.array(journal_dock.star_pos)
            dist_from_origin = numpy.linalg.norm(coords - self._origin)
            if (
                station_type in self.config.acceptable_station_types
                and dist_from_origin <= self.config.max_from_origin
                and journal_dock.dist_from_star_ls is not None
                and journal_dock.dist_from_star_ls <= self.config.max_from_sun
            ):
                cost_snapshot = CostSnapshot(
                    system_name=system,
                    station_name=station,
                    timestamp=message.timestamp,
                    buy_price=eddn_commodity.buy_price,
                    stock=eddn_commodity.stock,
                    sell_price=eddn_commodity.sell_price,
                    demand=eddn_commodity.demand,
                    market_id=journal_dock.market_id,
                    star_pos=journal_dock.star_pos,
                    station_type=station_type,
                    system_address=journal_dock.system_address,
                    dist_from_star_ls=journal_dock.dist_from_star_ls,
                    station_allegiance=journal_dock.station_allegiance,
                )

                self._insert_buy(stock_commodity, cost_snapshot)
                self._insert_sell(stock_commodity, cost_snapshot)

    def _insert_buy(self, stock_commodity: StockCommodity, cost_snapshot: CostSnapshot):
        # Remove any existing results
        for i in range(len(stock_commodity.best_buys) - 1, -1, -1):
            buy = stock_commodity.best_buys[i]
            if (
                buy.system_name == cost_snapshot.system_name
                and buy.station_name == cost_snapshot.station_name
            ):
                stock_commodity.best_buys.pop(i)

        # No buyable price, so not for sale
        if cost_snapshot.buy_price == 0:
            return

        # Check supply, ignore if too low
        if cost_snapshot.stock < self.config.min_stock:
            return

        # Put lowest prices first
        i = 0
        while i < len(stock_commodity.best_buys):
            if cost_snapshot.buy_price < stock_commodity.best_buys[i].buy_price:
                break
            i += 1
        stock_commodity.best_buys.insert(i, cost_snapshot)

        # Trim excess results
        stock_commodity.best_buys = stock_commodity.best_buys[: self.config.max_best]

    def _insert_sell(
        self, stock_commodity: StockCommodity, cost_snapshot: CostSnapshot
    ):
        # Remove any existing results
        for i in range(len(stock_commodity.best_sales) - 1, -1, -1):
            sale = stock_commodity.best_sales[i]
            if (
                sale.system_name == cost_snapshot.system_name
                and sale.station_name == cost_snapshot.station_name
            ):
                stock_commodity.best_sales.pop(i)

        # No sellable price, so not wanted
        if cost_snapshot.sell_price == 0:
            return

        # Check demand, ignore if too low
        if cost_snapshot.demand < self.config.min_demand:
            return

        # Put highest prices first
        i = 0
        while i < len(stock_commodity.best_sales):
            if cost_snapshot.sell_price > stock_commodity.best_sales[i].sell_price:
                break
            i += 1
        stock_commodity.best_sales.insert(i, cost_snapshot)
        # Trim excess results
        stock_commodity.best_sales = stock_commodity.best_sales[: self.config.max_best]
