from dataclasses import dataclass
from datetime import datetime

@dataclass
class ParsedLogEntry:
    original_timestamp: datetime
    timestamp: datetime
    level: str
    message: str
