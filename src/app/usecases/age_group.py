from app.services.age_group import AgeGroupService
from domain.age_group import AgeGroup


class AgeGroupUseCase:
    """Use case layer for age group operations."""

    def __init__(self, service: AgeGroupService):
        """Initialize use case with service dependency.

        Args:
            service: Service for age group operations
        """
        self._svc = service

    async def create(self, name: str, min_age: int, max_age: int) -> AgeGroup:
        """Create new age group.

        Args:
            name: Name of the age group
            min_age: Minimum age for the group
            max_age: Maximum age for the group

        Returns:
            Created age group
        """
        return await self._svc.create(name, min_age, max_age)

    async def delete(self, name: str) -> None:
        """Delete age group by name.

        Args:
            name: Name of the age group to delete
        """
        await self._svc.delete(name)

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[AgeGroup]:
        """List age groups with pagination.

        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of age groups
        """
        return await self._svc.list(offset=offset, limit=limit)

    async def count(self) -> int:
        """Count total number of age groups.

        Returns:
            Total number of age groups
        """
        return await self._svc.count()
