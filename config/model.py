from dataclasses import dataclass, field


@dataclass
class Config:
    eddn_relay_url: str
    eddn_timeout: int
    cmd_line_print_wait: int
    dock_file_path: str
    stock_file_path: str
