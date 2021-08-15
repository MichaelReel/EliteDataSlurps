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


def save(summary: Config):
    with open(__stock_file, "w") as json_file:
        data = ConfigSchema().dump(summary)
        json.dump(obj=data, fp=json_file, indent=4)
