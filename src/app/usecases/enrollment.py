from __future__ import annotations

from typing import Any, Protocol

from app.services.enrollment import EnrollmentService
from domain.enrollment import Enrollment


class EnrollmentPublisher(Protocol):
    def publish(self, payload: dict[str, Any]) -> None: ...


class EnrollmentUseCase:
    """Use case layer for enrollment operations."""
    
    def __init__(self, service: EnrollmentService, publisher: EnrollmentPublisher) -> None:
        """Initialize use case with service and publisher dependencies.
        
        Args:
            service: Service for enrollment operations
            publisher: Publisher for enrollment events
        """
        self._svc = service
        self._publisher = publisher

    async def request(self, *, name: str, age: int, cpf: str) -> None:
        """Request enrollment and publish if successful.
        
        Args:
            name: Student name for enrollment
            age: Student age for age group matching
            cpf: Student CPF for duplicate checking
        """
        payload = await self._svc.prepare_request(name=name, age=age, cpf=cpf)
        if payload:
            self._publisher.publish(payload)

    async def status(self, *, cpf: str) -> Enrollment | None:
        """Find enrollment by CPF.
        
        Args:
            cpf: CPF to search for
            
        Returns:
            Enrollment if found, None otherwise
        """
        return await self._svc.status(cpf=cpf)
