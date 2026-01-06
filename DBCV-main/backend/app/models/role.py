from enum import Enum, auto
from typing import Type


class RoleType(Enum):
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    USER = "USER"

    @classmethod
    def priority(cls, role: Type["RoleType"]) -> int:
        priority_range = [
            cls.ADMIN,
            cls.DEVELOPER,
            cls.USER
        ]
        return priority_range.index(role)
