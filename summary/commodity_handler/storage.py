import json

from summary.model import StockSummary
from summary.schema import StockSummarySchema


__stock_file = "stockfile.json"


def load() -> StockSummary:
    try:
        with open(__stock_file) as json_file:
            data = json.load(json_file)
            return StockSummarySchema().load(data)
    except FileNotFoundError:
        return StockSummary()


def save(summary: StockSummary):
    with open(__stock_file, "w") as json_file:
        data = StockSummarySchema().dump(summary)
        json.dump(obj=data, fp=json_file, indent=4)
