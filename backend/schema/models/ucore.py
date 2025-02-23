from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Ucore:
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
