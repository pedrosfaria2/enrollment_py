from app.services.age_group import AgeGroupService
from domain.age_group import AgeGroup


class AgeGroupUseCase:
    def __init__(self, service: AgeGroupService):
        self._svc = service

    async def create(self, name: str, min_age: int, max_age: int) -> AgeGroup:
        return await self._svc.create(name, min_age, max_age)

    async def delete(self, name: str) -> None:
        await self._svc.delete(name)

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[AgeGroup]:
        return await self._svc.list(offset=offset, limit=limit)

    async def count(self) -> int:
        return await self._svc.count()
