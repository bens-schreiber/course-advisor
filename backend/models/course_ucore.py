from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CourseUcore:
    id: int
    course_id: int
    ucore_id: int
    created_at: datetime
    updated_at: datetime
