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

    requested_at: int | None = None
    enrolled_at: int | None = None
    age_group_name: str | None = None

    def __post_init__(self) -> None:
        if self.age < 0:
            raise ValueError("age must be non-negative")
        if not _CPF_RE.match(self.cpf):
            raise ValueError("cpf must match 999.999.999-99 format")
        if self.status == EnrollmentStatus.APPROVED and self.enrolled_at is None:
            raise ValueError("enrolled_at must be set when status is APPROVED")

    @staticmethod
    def create_final(
        name: str,
        age: int,
        cpf: str,
        final_status: EnrollmentStatus,
        existing: Enrollment | None,
        *,
        requested_at: int | None = None,
        enrolled_at: int | None = None,
        age_group_name: str | None = None,
    ) -> Enrollment:
        """
        One-per-CPF + retry:
        - None -> create final
        - existing.APPROVED -> return existing (no-op)
        - existing.REJECTED -> replace with new final
        """
        candidate = Enrollment(
            name=name,
            age=age,
            cpf=cpf,
            status=final_status,
            requested_at=requested_at,
            enrolled_at=enrolled_at,
            age_group_name=age_group_name,
        )
        if existing is None:
            return candidate
        if existing.status == EnrollmentStatus.APPROVED:
            return existing
        # REJECTED or anything else -> accept new final
        return candidate
