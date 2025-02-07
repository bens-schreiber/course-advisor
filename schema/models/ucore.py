from dataclasses import dataclass


@dataclass(frozen=True)
class Ucore:
    id: int
    name: str
