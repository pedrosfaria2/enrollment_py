from __future__ import annotations

from collections.abc import Sequence

from domain.enrollment import Enrollment
from infra.enumerators.enrollment import EnrollmentStatus
from infra.repositories.enrollment import EnrollmentRepository


class EnrollmentAdminService:
    def __init__(self, repo: EnrollmentRepository) -> None:
        self._repo = repo

    async def get_by_cpf(self, *, cpf: str) -> Enrollment | None:
        return self._repo.find_by_cpf(cpf)

    async def list_by_age_group(self, *, name: str, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        return self._repo.search_by_fields(offset=offset, limit=limit, age_group_name=name)

    async def count_by_age_group(self, *, name: str) -> int:
        return self._repo.count(age_group_name=name)

    async def list_by_name(self, *, name: str, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        return self._repo.search_by_fields(offset=offset, limit=limit, name=name)

    async def count_by_name(self, *, name: str) -> int:
        return self._repo.count(name=name)

    async def list_by_status(
        self, *, status: EnrollmentStatus, offset: int = 0, limit: int = 100
    ) -> Sequence[Enrollment]:
        return self._repo.search_by_fields(offset=offset, limit=limit, status=status.value)

    async def count_by_status(self, *, status: EnrollmentStatus) -> int:
        return self._repo.count(status=status.value)

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        return self._repo.get_all(offset=offset, limit=limit)

    async def count_all(self) -> int:
        return self._repo.count()
