from __future__ import annotations

from app.services.enrollment import EnrollmentService
from app.usecases.enrollment import EnrollmentUseCase
from infra.messaging.rabbitmq import RabbitPublisher
from infra.repositories.age_group import AgeGroupRepository
from infra.repositories.enrollment import EnrollmentRepository

_publisher = RabbitPublisher()


def provide_use_case() -> EnrollmentUseCase:
    """Provide enrollment use case with all dependencies.

    Creates and configures an EnrollmentUseCase with required repositories,
    services, and messaging publisher for enrollment operations.

    Returns:
        Configured enrollment use case
    """
    svc = EnrollmentService(
        age_groups=AgeGroupRepository(),
        enrollments=EnrollmentRepository(),
    )
    return EnrollmentUseCase(service=svc, publisher=_publisher)
