from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, params, status

from app.usecases.age_group import AgeGroupUseCase
from domain.age_group import AgeGroupOverlapError, DuplicateAgeGroupError
from infra.common.logging import LogAPIRoute
from infra.dependencies.age_groups import provide_use_case
from infra.schemas.age_group import AgeGroup as AgeGroupDTO
from infra.schemas.pagination import PageResult
from infra.utils.pagination import Pagination


class AgeGroupAPI:
    TAGS = ["Age Groups"]
    PREFIX = "/age-groups"

    def __init__(
        self,
        app: FastAPI,
        *,
        dependencies: Sequence[params.Depends] | None = None,
    ) -> None:
        self.router = APIRouter(
            dependencies=list(dependencies) if dependencies else None,
            route_class=LogAPIRoute,
        )
        self._register_routes()
        app.include_router(self.router, prefix=self.PREFIX, tags=list(self.TAGS))

    def _register_routes(self) -> None:
        self.router.add_api_route(
            "/",
            self.list_groups,
            methods=["GET"],
            response_model=PageResult[AgeGroupDTO],
            summary="List age groups",
        )
        self.router.add_api_route(
            "/",
            self.create_group,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            response_model=AgeGroupDTO,
            summary="Create age group",
        )
        self.router.add_api_route(
            "/{name}",
            self.delete_group,
            methods=["DELETE"],
            status_code=status.HTTP_204_NO_CONTENT,
            response_model=None,
            summary="Delete age group",
        )

    async def list_groups(
        self,
        request: Request,
        uc: Annotated[AgeGroupUseCase, Depends(provide_use_case)],
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(gt=0)] = 100,
    ) -> PageResult[AgeGroupDTO]:
        offset = (page - 1) * page_size
        limit = page_size

        total_items = await uc.count()
        domain_items = await uc.list(offset=offset, limit=limit)

        dto_items = [
            AgeGroupDTO(
                name=item.name,
                min_age=item.age_range.min_age,
                max_age=item.age_range.max_age,
            )
            for item in domain_items
        ]

        return Pagination[AgeGroupDTO].create(
            request=request,
            items=dto_items,
            total_items=total_items,
            page=page,
            page_size=page_size,
            schema_class=AgeGroupDTO,
        )

    async def create_group(
        self,
        group: AgeGroupDTO,
        uc: Annotated[AgeGroupUseCase, Depends(provide_use_case)],
    ) -> AgeGroupDTO:
        try:
            domain_group = await uc.create(group.name, group.min_age, group.max_age)
            return AgeGroupDTO(
                name=domain_group.name,
                min_age=domain_group.age_range.min_age,
                max_age=domain_group.age_range.max_age,
            )
        except (DuplicateAgeGroupError, AgeGroupOverlapError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    async def delete_group(
        self,
        name: str,
        uc: Annotated[AgeGroupUseCase, Depends(provide_use_case)],
    ) -> None:
        try:
            await uc.delete(name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
