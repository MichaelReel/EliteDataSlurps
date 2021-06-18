from dataclasses import dataclass
from typing import List


@dataclass
class CostSnapshot:
    system_name: str
    station_name: str
    timestamp: str
    buy_price: int
    stock: int
    sell_price: int
    demand: int


@dataclass
class Commodity:
    name: str
    best_buys: List[CostSnapshot]
    best_sales: List[CostSnapshot]


@dataclass
class StockSummary:
    commodities: List[Commodity]
