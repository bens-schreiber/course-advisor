from dataclasses import dataclass

from schema.models import Rate


@dataclass(frozen=True)
class ProfessorCourseRating:
    id: int
    professor_id: int
    course_id: int
    rating: Rate
    course_rmp_quality: Rate
