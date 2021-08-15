from dataclasses import dataclass, field


@dataclass
class Config:
    eddn_relay_url: str = "tcp://eddn.edcd.io:9500"
    eddn_timeout: int = 60000
    cmd_line_print_wait: int = 20
