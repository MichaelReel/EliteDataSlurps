import io
import numpy

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

from config.model import CmdLineConfig
from eddn.commodity_v3.model import Commodity
from summary.model import CostSnapshot, StockSummary


class Output:
    def __init__(self, config: CmdLineConfig, target: StockSummary):
        self.config = config
        self.commodity_summary = target

    def get_highest_trade_diffs_str(self) -> str:
        best_trades = {}
        for commodity in self.commodity_summary.commodities:
            if commodity.best_buys and commodity.best_sales:
                key = float(
                    commodity.best_sales[0].sell_price
                    - commodity.best_buys[0].buy_price
                )
                while key in best_trades:
                    key -= 0.001
                best_trades[key] = commodity

        ret_io = io.StringIO()
        top_five_keys = sorted(best_trades.keys(), reverse=True)[:5]

        print_time = datetime.now().astimezone()
        print_time = print_time.replace(microsecond=0)

        print(f"-{f'- {print_time.isoformat()} -':=^104}-", file=ret_io)
        for key in top_five_keys:
            commodity: Commodity = best_trades[key]
            top_buy_from: CostSnapshot = commodity.best_buys[0]
            top_sell_to: CostSnapshot = commodity.best_sales[0]
            distance: float = get_trade_distance(top_buy_from, top_sell_to)
            print(
                f"  {commodity.name.upper()}  (Best: profit per unit: {key}, Distance: {distance:.2f} ly):",
                file=ret_io,
            )
            for buy_from in commodity.best_buys[::-1]:
                buy_age = relativedelta(print_time, parse(buy_from.timestamp))
                distance: float = get_trade_distance(buy_from, top_sell_to)
                station_highlight = self.config.station_highlights.get(
                    buy_from.station_type.lower(), " "
                )
                print(
                    f"Buy  @{buy_from.buy_price:7d}"
                    f" <  {buy_from.system_name: >26}"
                    f" {buy_from.station_name[:24]: >24}"
                    f" {station_highlight}"
                    f" {distance:6.2f} ly"
                    f" {buy_from.dist_from_star_ls or 0:9.2f} ls"
                    f"{f' {buy_age.days:2d}d' if buy_age.days else '    '}"
                    f" {buy_age.hours:02d}:{buy_age.minutes:02d}:{buy_age.seconds:02d}",
                    file=ret_io,
                )

            for sell_to in commodity.best_sales:
                sell_age = relativedelta(print_time, parse(sell_to.timestamp))
                distance: float = get_trade_distance(top_buy_from, sell_to)
                station_highlight = self.config.station_highlights.get(
                    sell_to.station_type.lower(), " "
                )
                print(
                    f"Sell @{sell_to.sell_price:7d}"
                    f"  > {sell_to.system_name: >26}"
                    f" {sell_to.station_name[:24]: >24}"
                    f" {station_highlight}"
                    f" {distance:6.2f} ly"
                    f" {sell_to.dist_from_star_ls or 0:9.2f} ls"
                    f"{f' {sell_age.days:2d}d' if sell_age.days else '    '}"
                    f" {sell_age.hours:02d}:{sell_age.minutes:02d}:{sell_age.seconds:02d}",
                    file=ret_io,
                )
            print("-" * 106, file=ret_io)

        return ret_io.getvalue()


def get_trade_distance(_from: CostSnapshot, _to: CostSnapshot) -> float:
    a = numpy.array(_from.star_pos)
    b = numpy.array(_to.star_pos)
    return numpy.linalg.norm(a - b)
