import json

from config.model import Config
from summary.model import DockSummary
from summary.schema import DockSummarySchema


def load(dock_file: str) -> DockSummary:
    try:
        with open(dock_file) as json_file:
            data = json.load(json_file)
            return DockSummarySchema().load(data)
    except FileNotFoundError:
        return DockSummary()


def save(dock_file: str, summary: DockSummary):
    with open(dock_file, "w") as json_file:
        data = DockSummarySchema().dump(summary)
        json.dump(obj=data, fp=json_file, indent=4)
