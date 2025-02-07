from dataclasses import dataclass

from schema.models.util import Rating


@dataclass(frozen=True)
class Professor:
    id: int
    department_id: int
    name: str
    rmp_quality: Rating
    rmp_difficulty: Rating
    rmp_take_again: float
    rmp_rating_count: int
