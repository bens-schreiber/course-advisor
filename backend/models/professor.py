from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class _Professor:
    id: int
    department_id: int
    name: str
    created_at: datetime
    updated_at: datetime
