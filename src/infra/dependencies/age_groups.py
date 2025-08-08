from app.services.age_group import AgeGroupService
from app.usecases.age_group import AgeGroupUseCase
from infra.repositories.age_group import AgeGroupRepository


def provide_use_case() -> AgeGroupUseCase:
    repo = AgeGroupRepository()
    service = AgeGroupService(repo)
    return AgeGroupUseCase(service)
