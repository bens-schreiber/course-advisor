from dataclasses import dataclass

from schema.models import Rate


@dataclass(frozen=True)
class Rating:
    id: int
    professor_id: int
    course_id: int
    rating: Rate
    rmp_quality: Rate
    rmp_difficulty: Rate
    rmp_comment: str
