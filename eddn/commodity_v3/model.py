from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Header:
    uploader_id: str
    software_name: str
    software_version: str
    gateway_timestamp: str


@dataclass
class Commodity:
    name: str
    mean_price: int
    buy_price: int
    stock: int
    stock_bracket: str
    sell_price: int
    demand: int
    demand_bracket: str
    status_flags: Optional[List[str]] = None


@dataclass
class Economy:
    name: str
    proportion: float


@dataclass
class Message:
    system_name: str
    station_name: str
    market_id: int
    timestamp: str
    commodities: List[Commodity]

    economies: Optional[List[Economy]] = None
    prohibited: Optional[List[str]] = None
    horizons: Optional[bool] = None
    odyssey: Optional[bool] = None


@dataclass
class CommodityV3:
    header: Header
    message: Message
