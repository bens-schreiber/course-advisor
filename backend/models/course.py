from dataclasses import dataclass
from datetime import datetime

from backend.models import ClassLevel, Credit


@dataclass(frozen=True)
class Course:
    id: int
    name: str
    credits: Credit
    level: ClassLevel
    created_at: datetime
    updated_at: datetime
