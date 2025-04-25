from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class _Professor:
    name: str
    department_id: int
    rate_my_query_id: int

