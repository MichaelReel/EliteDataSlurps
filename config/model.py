from dataclasses import dataclass, field


@dataclass
class DockConfig:
    file_path: str
    autosave_wait: int


@dataclass
class StockConfig:
    file_path: str
    autosave_wait: int


@dataclass
class Config:
    eddn_relay_url: str
    eddn_timeout: int
    cmd_line_print_wait: int
    dock: DockConfig
    stock: StockConfig
