from __future__ import annotations

import time

from domain.enrollment import Enrollment, EnrollmentStatus
from infra.repositories.age_group import AgeGroupRepository
from infra.repositories.enrollment import EnrollmentRepository


class EnrollmentService:
    """Service layer for enrollment operations.

    Handles enrollment creation and status retrieval.
    """

    def __init__(self, age_groups: AgeGroupRepository, enrollments: EnrollmentRepository) -> None:
        """Initialize service with repository dependencies.

        Args:
            age_groups: Repository for age group data operations
            enrollments: Repository for enrollment data operations
        """
        self._age_groups = age_groups
        self._enrollments = enrollments

    async def prepare_request(self, *, name: str, age: int, cpf: str) -> dict[str, object] | None:
        """Prepare enrollment request with age group validation.

        Args:
            name: Student name for enrollment
            age: Student age for age group matching
            cpf: Student CPF for duplicate checking

        Returns:
            Enrollment data dictionary if successful, None if already approved
        """
        group = self._age_groups.find_covering(age)
        if group is None:
            raise ValueError("no age group covers this age")

        existing = self._enrollments.find_by_cpf(cpf)

        if existing and existing.status == EnrollmentStatus.APPROVED:
            raise PermissionError("enrollment already approved for this CPF")

        e = Enrollment.create_final(
            name=name,
            age=age,
            cpf=cpf,
            final_status=EnrollmentStatus.PENDING,
            existing=existing,
            requested_at=int(time.time()),
            enrolled_at=None,
            age_group_name=group.name,
        )

        if existing and existing.status == EnrollmentStatus.APPROVED and e is existing:
            return None

        return {
            "name": e.name,
            "age": e.age,
            "cpf": e.cpf,
            "requested_at": e.requested_at,
            "age_group_name": e.age_group_name,
            "status": e.status.value,
        }

    async def status(self, *, cpf: str) -> Enrollment | None:
        """Find enrollment by CPF.

        Args:
            cpf: CPF to search for

        Returns:
            Enrollment if found, None otherwise
        """
        return self._enrollments.find_by_cpf(cpf)
