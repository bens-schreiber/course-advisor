from dataclasses import dataclass

from schema.models.util import Rating


@dataclass(frozen=True)
class Rating:
    id: int
    professor_id: int
    course_id: int
    rating: Rating
    rmp_quality: Rating
    rmp_difficulty: Rating
    rmp_comment: str
