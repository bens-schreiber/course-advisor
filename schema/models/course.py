from dataclasses import dataclass
from schema.models.util import ClassLevel, Credit


@dataclass(frozen=True)
class Course:
    id: int
    name: str
    credits: Credit
    level: ClassLevel
