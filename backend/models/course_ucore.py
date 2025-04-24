from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CourseUCore:
    course_id: str  # e.g., HIST 105
    ucore_designation: str  # e.g., ROOTS
    course_name: str
    credits: str
    created_at: datetime = datetime.now()
