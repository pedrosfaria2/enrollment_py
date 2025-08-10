from __future__ import annotations

from app.services.age_group import AgeGroupService
from app.usecases.age_group import AgeGroupUseCase
from infra.repositories.age_group import AgeGroupRepository
from infra.repositories.enrollment import EnrollmentRepository


def provide_use_case() -> AgeGroupUseCase:
    """Provide age group use case with all dependencies.
    
    Creates and configures an AgeGroupUseCase with required repositories
    and services for age group operations.
    
    Returns:
        Configured age group use case
    """
    age_groups = AgeGroupRepository()
    enrollments = EnrollmentRepository()
    service = AgeGroupService(repo=age_groups, enrollments=enrollments)
    return AgeGroupUseCase(service)
