from dataclasses import dataclass, field
from typing import List


@dataclass
class DockConfig:
    file_path: str
    autosave_wait: int


@dataclass
class StockConfig:
    file_path: str
    autosave_wait: int
    max_best: int
    min_stock: int
    min_demand: int
    acceptable_station_types: List[str]
    origin_coords: List[float]
    max_from_origin: float


@dataclass
class Config:
    eddn_relay_url: str
    eddn_timeout: int
    cmd_line_print_wait: int
    dock: DockConfig
    stock: StockConfig
