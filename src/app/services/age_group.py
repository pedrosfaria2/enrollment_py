from domain.age_group import AgeGroup
from infra.repositories.age_group import AgeGroupRepository


class AgeGroupService:
    def __init__(self, repo: AgeGroupRepository):
        self._repo = repo

    async def create(self, name: str, min_age: int, max_age: int) -> AgeGroup:
        conflicts = self._repo.find_overlapping(min_age=min_age, max_age=max_age)
        entity = AgeGroup.create(name, min_age, max_age, conflicts)
        self._repo.insert(entity)
        return entity

    async def delete(self, name: str) -> None:
        if not self._repo.exists(name=name):
            raise KeyError("age group not found")
        self._repo.remove(name=name)

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[AgeGroup]:
        return self._repo.get_all(offset=offset, limit=limit)

    async def count(self) -> int:
        return self._repo.count()
