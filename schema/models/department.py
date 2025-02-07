from dataclasses import dataclass


@dataclass(frozen=True)
class Department:
    id: int
    name: str
