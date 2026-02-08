from __future__ import annotations

from enum import Enum


class RoleName(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    ADMIN = "admin"