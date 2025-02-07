from dataclasses import dataclass

from schema.models.util import Rating


@dataclass(frozen=True)
class ProfessorCourseRating:
    id: int
    professor_id: int
    course_id: int
    rating: Rating
    course_rmp_quality: Rating
