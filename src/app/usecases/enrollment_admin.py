from __future__ import annotations

from collections.abc import Sequence

from app.services.enrollment_admin import EnrollmentAdminService
from domain.enrollment import Enrollment, EnrollmentStatus


class EnrollmentAdminUseCase:
    def __init__(self, service: EnrollmentAdminService) -> None:
        self._svc = service

    async def get_by_cpf(self, *, cpf: str) -> Enrollment | None:
        return await self._svc.get_by_cpf(cpf=cpf)

    async def list_by_age_group(self, *, name: str, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        return await self._svc.list_by_age_group(name=name, offset=offset, limit=limit)

    async def count_by_age_group(self, *, name: str) -> int:
        return await self._svc.count_by_age_group(name=name)

    async def list_by_name(self, *, name: str, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        return await self._svc.list_by_name(name=name, offset=offset, limit=limit)

    async def count_by_name(self, *, name: str) -> int:
        return await self._svc.count_by_name(name=name)

    async def list_by_status(
        self, *, status: EnrollmentStatus, offset: int = 0, limit: int = 100
    ) -> Sequence[Enrollment]:
        return await self._svc.list_by_status(status=status, offset=offset, limit=limit)

    async def count_by_status(self, *, status: EnrollmentStatus) -> int:
        return await self._svc.count_by_status(status=status)

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> Sequence[Enrollment]:
        return await self._svc.get_all(offset=offset, limit=limit)

    async def count_all(self) -> int:
        return await self._svc.count_all()
