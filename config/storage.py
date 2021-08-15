import json

from config.model import Config
from config.schema import ConfigSchema


def load(config_file: str) -> Config:
    try:
        with open(config_file) as json_file:
            data = json.load(json_file)
            return ConfigSchema().load(data)
    except FileNotFoundError:
        return Config()
