from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Header:
    uploader_id: str
    software_name: str
    software_version: str
    gateway_timestamp: datetime


@dataclass
class Message:
    event: str
    star_pos: List[float]
    system_name: str
    system_address: int
    timestamp: datetime

    dist_from_star_ls: Optional[float] = None
    market_id: Optional[int] = None
    station_allegiance: Optional[str] = None
    station_name: Optional[str] = None
    station_type: Optional[str] = None


@dataclass
class JournalV1():
    header: Header
    message: Message