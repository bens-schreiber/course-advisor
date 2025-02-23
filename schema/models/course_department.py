from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CourseDepartment:
    id: int
    course_id: int
    department_id: int
    created_at: datetime
    updated_at: datetime
