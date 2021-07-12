from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class CostSnapshot:
    system_name: str
    station_name: str
    timestamp: str
    buy_price: int
    stock: int
    sell_price: int
    demand: int

    market_id: Optional[int] = None
    star_pos: Optional[List[float]] = None
    station_type: Optional[str] = None
    system_address: Optional[int] = None
    dist_from_star_ls: Optional[float] = None
    station_allegiance: Optional[str] = None


@dataclass
class Commodity:
    name: str
    best_buys: List[CostSnapshot]
    best_sales: List[CostSnapshot]


@dataclass
class StockSummary:
    commodities: List[Commodity] = field(default_factory=list)


@dataclass
class Station:
    market_id: int
    star_pos: List[float]
    station_name: str
    station_type: str
    system_address: int
    system_name: str
    timestamp: datetime
    dist_from_star_ls: Optional[float] = None
    station_allegiance: Optional[str] = None


@dataclass
class DockSummary:
    stations: Dict[str, Station] = field(default_factory=dict)
