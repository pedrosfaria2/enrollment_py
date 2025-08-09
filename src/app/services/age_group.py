from domain.age_group import AgeGroup, AgeGroupInUseError, DuplicateAgeGroupError
from infra.repositories.age_group import AgeGroupRepository
from infra.repositories.enrollment import EnrollmentRepository


class AgeGroupService:
    def __init__(self, repo: AgeGroupRepository, enrollments: EnrollmentRepository):
        self._repo = repo
        self._enrollments = enrollments

    async def create(self, name: str, min_age: int, max_age: int) -> AgeGroup:
        if self._repo.exists(name=name):
            raise DuplicateAgeGroupError(f"Age group '{name}' already exists.")
        conflicts = self._repo.find_overlapping(min_age=min_age, max_age=max_age)
        entity = AgeGroup.create(name, min_age, max_age, conflicts)
        self._repo.insert(entity)
        return entity

    async def delete(self, name: str) -> None:
        if not self._repo.exists(name=name):
            raise KeyError("age group not found")
        if self._enrollments.exists_by_age_group(name, only_approved=True):
            raise AgeGroupInUseError(f"age group '{name}' has approved enrollments")
        self._repo.remove(name=name)

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[AgeGroup]:
        return self._repo.get_all(offset=offset, limit=limit)

    async def count(self) -> int:
        return self._repo.count()
