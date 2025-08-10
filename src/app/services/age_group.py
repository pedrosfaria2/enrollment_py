from domain.age_group import AgeGroup, AgeGroupInUseError, DuplicateAgeGroupError
from infra.repositories.age_group import AgeGroupRepository
from infra.repositories.enrollment import EnrollmentRepository


class AgeGroupService:
    """Service layer for age group operations providing business logic and validation.
    
    Handles creation, deletion, listing and counting of age groups with proper
    validation of business rules including name uniqueness, range overlap detection,
    and prevention of deletion when age groups are in use by approved enrollments.
    """
    
    def __init__(self, repo: AgeGroupRepository, enrollments: EnrollmentRepository):
        """Initialize service with repository dependencies.
        
        Args:
            repo: Repository for age group data operations
            enrollments: Repository for enrollment data to check usage
        """
        self._repo = repo
        self._enrollments = enrollments

    async def create(self, name: str, min_age: int, max_age: int) -> AgeGroup:
        """Create a new age group with validation.
        
        Validates that the name is unique and the age range doesn't overlap
        with existing age groups. Creates and persists the new age group.
        
        Args:
            name: Unique name for the age group
            min_age: Minimum age for the range (inclusive)
            max_age: Maximum age for the range (inclusive)
            
        Returns:
            The created AgeGroup entity
        """
        if self._repo.exists(name=name):
            raise DuplicateAgeGroupError(f"Age group '{name}' already exists.")
        conflicts = self._repo.find_overlapping(min_age=min_age, max_age=max_age)
        entity = AgeGroup.create(name, min_age, max_age, conflicts)
        self._repo.insert(entity)
        return entity

    async def delete(self, name: str) -> None:
        """Delete an age group after validating it's not in use.
        
        Checks that the age group exists and is not currently being used
        by any approved enrollments before removing it from storage.
        
        Args:
            name: Name of the age group to delete
        """
        if not self._repo.exists(name=name):
            raise KeyError("age group not found")
        if self._enrollments.exists_by_age_group(name, only_approved=True):
            raise AgeGroupInUseError(f"age group '{name}' has approved enrollments")
        self._repo.remove(name=name)

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[AgeGroup]:
        """Retrieve a paginated list of age groups.
        
        Returns age groups from the repository with pagination support
        for efficient data retrieval in large datasets.
        
        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)
            
        Returns:
            List of AgeGroup entities
        """
        return self._repo.get_all(offset=offset, limit=limit)

    async def count(self) -> int:
        """Get the total number of age groups in the system.
        
        Returns:
            Total count of age groups stored in the repository
        """
        return self._repo.count()
