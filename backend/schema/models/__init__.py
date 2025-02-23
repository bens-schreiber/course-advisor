from dataclasses import dataclass
from typing import TypeVar, Generic

T = TypeVar("T")


class __BoundedValue(Generic[T]):
    value: T

    def __post_init__(self):
        raise NotImplementedError

    def __init__(self, value: T, min_val: T, max_val: T):
        self.value = value
        if not (min_val <= value <= max_val):
            raise ValueError(f"must be between {min_val} and {max_val}")


@dataclass(frozen=True)
class Rate(__BoundedValue[float]):
    def __post_init__(self):
        super().__init__(self.value, 0.0, 5.0)


@dataclass(frozen=True)
class Credit(__BoundedValue[int]):
    def __post_init__(self):
        super().__init__(self.value, 1, 4)


@dataclass(frozen=True)
class ClassLevel(__BoundedValue[int]):
    def __post_init__(self):
        super().__init__(self.value, 100, 600)
