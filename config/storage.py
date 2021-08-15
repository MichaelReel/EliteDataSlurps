import json

from config.model import Config
from config.schema import ConfigSchema


__stock_file = "config.json"


def load() -> Config:
    try:
        with open(__stock_file) as json_file:
            data = json.load(json_file)
            return ConfigSchema().load(data)
    except FileNotFoundError:
        return Config()
