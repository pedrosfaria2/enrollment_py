from __future__ import annotations

from collections.abc import Sequence

from domain.enrollment import Enrollment
from infra.enumerators.enrollment import EnrollmentStatus
from infra.repositories.enrollment import EnrollmentRepository


class EnrollmentAdminService:
    """Service layer for enrollment query operations.

    Provides methods to find, list and count enrollments by different criteria.
    """

    def __init__(self, repo: EnrollmentRepository) -> None:
        """Initialize service with repository dependency.

        Args:
            repo: Repository for enrollment data operations
        """
        self._repo = repo

    async def get_by_cpf(self, *, cpf: str) -> Enrollment | None:
        """Find enrollment by CPF.

        Args:
            cpf: CPF to search for

        Returns:
            Enrollment if found, None otherwise
        """
        return self._repo.find_by_cpf(cpf)

    async def list_by_age_group(self, *, name: str, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        """List enrollments by age group name.

        Args:
            name: Age group name to filter by
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of enrollments matching the age group
        """
        return self._repo.search_by_fields(offset=offset, limit=limit, age_group_name=name)

    async def count_by_age_group(self, *, name: str) -> int:
        """Count enrollments by age group name.

        Args:
            name: Age group name to count for

        Returns:
            Number of enrollments in the age group
        """
        return self._repo.count(age_group_name=name)

    async def list_by_name(self, *, name: str, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        """List enrollments by student name.

        Args:
            name: Student name to filter by
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of enrollments matching the name
        """
        return self._repo.search_by_fields(offset=offset, limit=limit, name=name)

    async def count_by_name(self, *, name: str) -> int:
        """Count enrollments by student name.

        Args:
            name: Student name to count for

        Returns:
            Number of enrollments with the name
        """
        return self._repo.count(name=name)

    async def list_by_status(
        self, *, status: EnrollmentStatus, offset: int = 0, limit: int = 100
    ) -> Sequence[Enrollment]:
        """List enrollments by status.

        Args:
            status: Enrollment status to filter by
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of enrollments with the status
        """
        return self._repo.search_by_fields(offset=offset, limit=limit, status=status.value)

    async def count_by_status(self, *, status: EnrollmentStatus) -> int:
        """Count enrollments by status.

        Args:
            status: Enrollment status to count for

        Returns:
            Number of enrollments with the status
        """
        return self._repo.count(status=status.value)

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        """Get all enrollments.

        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of all enrollments
        """
        return self._repo.get_all(offset=offset, limit=limit)

    async def count_all(self) -> int:
        """Count all enrollments.

        Returns:
            Total number of enrollments
        """
        return self._repo.count()
