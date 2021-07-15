import io
import numpy

from datetime import datetime

from eddn.commodity_v3.model import Commodity
from summary.model import CostSnapshot, StockSummary


class Output:
    def __init__(self, target: StockSummary):
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

        print(f"{datetime.now().isoformat():=^99}-", file=ret_io)
        for key in top_five_keys:
            commodity: Commodity = best_trades[key]
            buy_from: CostSnapshot = commodity.best_buys[0]
            sell_to: CostSnapshot = commodity.best_sales[0]
            distance: float = get_trade_distance(buy_from, sell_to)
            print(
                f"{commodity.name.upper()} (Profit per unit: {key}, Distance: {distance:.2f} ly):",
                file=ret_io,
            )
            print(
                f"  Buy at  {buy_from.buy_price:=7d} from {buy_from.system_name: ^25} /"
                f" {buy_from.station_name: ^25} ({buy_from.station_type: ^10})"
                f" {buy_from.timestamp}",
                file=ret_io,
            )
            print(
                f"  Sell at {sell_to.sell_price:=7d}   to {sell_to.system_name: ^25} /"
                f" {sell_to.station_name: ^25} ({sell_to.station_type: ^10})"
                f" {sell_to.timestamp}",
                file=ret_io,
            )
            print("-" * 100, file=ret_io)

        return ret_io.getvalue()


def get_trade_distance(_from: CostSnapshot, _to: CostSnapshot) -> float:
    a = numpy.array(_from.star_pos)
    b = numpy.array(_to.star_pos)
    return numpy.linalg.norm(a - b)
