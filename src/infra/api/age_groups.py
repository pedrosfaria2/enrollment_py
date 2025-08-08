from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status

from app.usecases.age_group import AgeGroupUseCase
from domain.age_group import AgeGroup
from infra.dependencies.age_groups import provide_use_case
from infra.schemas.age_group import AgeGroup as AgeGroupDTO
from infra.schemas.pagination import PageResult
from infra.utils.pagination import Pagination


class AgeGroupAPI:
    TAGS: list[str] = ["Age Groups"]
    PREFIX = "/age-groups"

    def __init__(self, app: FastAPI) -> None:
        self.router = APIRouter()
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
            summary="Delete age group",
        )

    async def list_groups(
        self,
        request: Request,
        page: Annotated[int, Query(1, ge=1)],
        page_size: Annotated[int, Query(100, gt=0)],
        uc: Annotated[AgeGroupUseCase, Depends(provide_use_case)],
    ) -> PageResult[AgeGroupDTO]:
        offset = (page - 1) * page_size
        limit = page_size

        total_items = await uc.count()
        items = await uc.list(offset=offset, limit=limit)

        return Pagination[AgeGroupDTO].create(
            request=request,
            items=items,
            total_items=total_items,
            page=page,
            page_size=page_size,
            schema_class=AgeGroupDTO,
        )

    async def create_group(
        self,
        group: AgeGroupDTO,
        uc: Annotated[AgeGroupUseCase, Depends(provide_use_case)],
    ) -> AgeGroup:
        try:
            return await uc.create(group.name, group.min_age, group.max_age)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    async def delete_group(
        self,
        name: str,
        uc: Annotated[AgeGroupUseCase, Depends(provide_use_case)],
    ) -> None:
        try:
            await uc.delete(name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
