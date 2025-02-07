from dataclasses import dataclass


@dataclass(frozen=True)
class CourseDepartment:
    id: int
    course_id: int
    department_id: int
