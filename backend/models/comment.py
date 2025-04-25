from dataclasses import dataclass
from datetime import date
from selenium.webdriver.common.by import By


@dataclass(frozen=True)
class _Comment:
    course_name: str
    course_level: int
    quality: float
    difficulty: float
    comment: str
    date: date

    def level_frm_name(s):
        number = ""
        for char in s:
            if char.isdigit():
                number += char
            elif number:
                break
        return int(number) if number else None

