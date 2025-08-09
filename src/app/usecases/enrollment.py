from __future__ import annotations

from typing import Any, Protocol

from app.services.enrollment import EnrollmentService
from domain.enrollment import Enrollment


class EnrollmentPublisher(Protocol):
    def publish(self, payload: dict[str, Any]) -> None: ...


class EnrollmentUseCase:
    def __init__(self, service: EnrollmentService, publisher: EnrollmentPublisher) -> None:
        self._svc = service
        self._publisher = publisher

    async def request(self, *, name: str, age: int, cpf: str) -> None:
        payload = await self._svc.prepare_request(name=name, age=age, cpf=cpf)
        if payload:
            self._publisher.publish(payload)

    async def status(self, *, cpf: str) -> Enrollment | None:
        return await self._svc.status(cpf=cpf)
