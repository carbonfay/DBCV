from enum import Enum, auto
from typing import Type


class AccessType(Enum):
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"
    NO_ACCESS = "NO_ACCESS"

    @classmethod
    def priority(cls, role: Type["AccessType"]) -> int:
        priority_range = [
            cls.EDITOR,
            cls.VIEWER,
            cls.NO_ACCESS
        ]
        return priority_range.index(role)