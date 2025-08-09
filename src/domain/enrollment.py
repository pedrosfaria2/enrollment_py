from __future__ import annotations

import re
from dataclasses import dataclass, field

from infra.enumerators.enrollment import EnrollmentStatus

_CPF_RE = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")


class EnrollmentError(Exception): ...


class DuplicateEnrollmentError(EnrollmentError): ...


class IllegalTransitionError(EnrollmentError): ...


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

    @staticmethod
    def create_final(
        name: str,
        age: int,
        cpf: str,
        final_status: EnrollmentStatus,
        existing: Enrollment | None,
    ) -> Enrollment:
        """
        'One per CPF' + retry semantics:
        - If no existing -> create final record.
        - If existing.APPROVED -> keep existing (idempotent no-op).
        - If existing.REJECTED -> allow retry (replace with new final).
        """
        candidate = Enrollment(name=name, age=age, cpf=cpf, status=final_status)

        if existing is None:
            return candidate

        if existing.cpf != cpf:
            # different identity: this factory guards one CPF only
            return candidate

        if existing.status == EnrollmentStatus.APPROVED:
            return existing

        if existing.status == EnrollmentStatus.REJECTED:
            # retry allowed; accept new final (could be APPROVED or REJECTED)
            return candidate

        return candidate
