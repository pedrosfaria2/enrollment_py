from __future__ import annotations

import re
from dataclasses import dataclass, field

from infra.enumerators.enrollment import EnrollmentStatus

_CPF_RE = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")


class EnrollmentError(Exception):
    """Base exception for enrollment related errors."""
    ...


class DuplicateEnrollmentError(EnrollmentError):
    """Raised when attempting to create a duplicate enrollment for the same CPF."""
    ...


class IllegalTransitionError(EnrollmentError):
    """Raised when attempting an invalid status transition for an enrollment."""
    ...


@dataclass(slots=True, frozen=True)
class Enrollment:
    """Student enrollment with validation and status management."""
    name: str
    age: int
    cpf: str
    status: EnrollmentStatus = field(default=EnrollmentStatus.PENDING)

    requested_at: int | None = None
    enrolled_at: int | None = None
    age_group_name: str | None = None

    def __post_init__(self) -> None:
        """Validate age ≥ 0, CPF format, and enrolled_at when APPROVED."""
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
        """Create/update enrollment with one-per-CPF policy. Returns existing if APPROVED."""
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
