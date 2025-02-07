from dataclasses import dataclass


@dataclass(frozen=True)
class CourseUcore:
    id: int
    course_id: int
    ucore_id: int
