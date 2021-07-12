import json

from summary.model import DockSummary
from summary.schema import DockSummarySchema


__stock_file = "dockfile.json"


def load() -> DockSummary:
    try:
        with open(__stock_file) as json_file:
            data = json.load(json_file)
            return DockSummarySchema().load(data)
    except FileNotFoundError:
        return DockSummary()


def save(summary: DockSummary):
    with open(__stock_file, "w") as json_file:
        data = DockSummarySchema().dump(summary)
        json.dump(data, json_file)
