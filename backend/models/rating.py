from dataclasses import dataclass
from datetime import datetime

from backend.models import Rate


@dataclass(frozen=True)
class Rating:
    id: int
    professor_id: int
    course_id: int
    rmp_quality: Rate
    rmp_difficulty: Rate
    rmp_comment: str
    created_at: datetime
    updated_at: datetime
