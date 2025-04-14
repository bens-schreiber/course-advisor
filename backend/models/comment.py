from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Comment:
    course_name: str
    course_level: int
    quality: float
    difficulty: float
    comment: str
    date: date
