from dataclasses import dataclass
from datetime import datetime

from backend.models import Rate


@dataclass(frozen=True)
class ProfessorCumulativeRating:
    id: int
    professor_id: int
    rating: Rate
    created_at: datetime
    updated_at: datetime
