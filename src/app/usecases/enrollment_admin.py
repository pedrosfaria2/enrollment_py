from __future__ import annotations

from collections.abc import Sequence

from app.services.enrollment_admin import EnrollmentAdminService
from domain.enrollment import Enrollment, EnrollmentStatus


class EnrollmentAdminUseCase:
    """Use case layer for enrollment admin operations."""

    def __init__(self, service: EnrollmentAdminService) -> None:
        """Initialize use case with service dependency.

        Args:
            service: Service for enrollment admin operations
        """
        self._svc = service

    async def get_by_cpf(self, *, cpf: str) -> Enrollment | None:
        """Find enrollment by CPF.

        Args:
            cpf: CPF to search for

        Returns:
            Enrollment if found, None otherwise
        """
        return await self._svc.get_by_cpf(cpf=cpf)

    async def list_by_age_group(self, *, name: str, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        """List enrollments by age group name.

        Args:
            name: Age group name to filter by
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of enrollments matching the age group
        """
        return await self._svc.list_by_age_group(name=name, offset=offset, limit=limit)

    async def count_by_age_group(self, *, name: str) -> int:
        """Count enrollments by age group name.

        Args:
            name: Age group name to count for

        Returns:
            Number of enrollments in the age group
        """
        return await self._svc.count_by_age_group(name=name)

    async def list_by_name(self, *, name: str, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        """List enrollments by student name.

        Args:
            name: Student name to filter by
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of enrollments matching the name
        """
        return await self._svc.list_by_name(name=name, offset=offset, limit=limit)

    async def count_by_name(self, *, name: str) -> int:
        """Count enrollments by student name.

        Args:
            name: Student name to count for

        Returns:
            Number of enrollments with the name
        """
        return await self._svc.count_by_name(name=name)

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
        return await self._svc.list_by_status(status=status, offset=offset, limit=limit)

    async def count_by_status(self, *, status: EnrollmentStatus) -> int:
        """Count enrollments by status.

        Args:
            status: Enrollment status to count for

        Returns:
            Number of enrollments with the status
        """
        return await self._svc.count_by_status(status=status)

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        """Get all enrollments.

        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of all enrollments
        """
        return await self._svc.get_all(offset=offset, limit=limit)

    async def count_all(self) -> int:
        """Count all enrollments.

        Returns:
            Total number of enrollments
        """
        return await self._svc.count_all()
