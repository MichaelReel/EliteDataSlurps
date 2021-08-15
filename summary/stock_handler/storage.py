import json

from summary.model import StockSummary
from summary.schema import StockSummarySchema


def load(stock_file: str) -> StockSummary:
    try:
        with open(stock_file) as json_file:
            data = json.load(json_file)
            return StockSummarySchema().load(data)
    except FileNotFoundError:
        return StockSummary()


def save(stock_file: str, summary: StockSummary):
    with open(stock_file, "w") as json_file:
        data = StockSummarySchema().dump(summary)
        json.dump(obj=data, fp=json_file, indent=4)
