from __future__ import annotations

from app.services.enrollment_admin import EnrollmentAdminService
from app.usecases.enrollment_admin import EnrollmentAdminUseCase
from infra.repositories.enrollment import EnrollmentRepository


def provide_admin_use_case() -> EnrollmentAdminUseCase:
    """Provide enrollment admin use case with all dependencies.

    Creates and configures an EnrollmentAdminUseCase with required repositories
    and services for enrollment administrative operations.

    Returns:
        Configured enrollment admin use case
    """
    repo = EnrollmentRepository()
    svc = EnrollmentAdminService(repo)
    return EnrollmentAdminUseCase(svc)
