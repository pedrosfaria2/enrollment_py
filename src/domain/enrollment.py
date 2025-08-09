from __future__ import annotations

import re
from dataclasses import dataclass, field

from infra.enumerators.enrollment import EnrollmentStatus

_CPF_RE = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")


@dataclass(slots=True, frozen=True)
class Enrollment:
    name: str
    age: int
    cpf: str
    status: EnrollmentStatus = field(default=EnrollmentStatus.PENDING)

    def __post_init__(self) -> None:
        if self.age < 0:
            raise ValueError("age must be non-negative")
        if not _CPF_RE.match(self.cpf):
            raise ValueError("cpf must match 999.999.999-99 format")
