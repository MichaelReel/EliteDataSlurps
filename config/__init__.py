from argparse import ArgumentParser
from config.storage import load as _load

parser = ArgumentParser()
parser.add_argument("--config", help="use an alternative config file", type=str, default="config.json")
parser.parse_args()

config = _load(config_file=parser.parse_args().config)
