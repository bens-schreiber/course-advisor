from dataclasses import dataclass
from datetime import datetime

from backend.models import Rate


@dataclass(frozen=True)
class ProfessorCourseRating:
    id: int
    professor_id: int
    course_id: int
    rating: Rate
    created_at: datetime
    updated_at: datetime
