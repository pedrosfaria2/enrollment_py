from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, params, status

from app.services.age_group import AgeGroupInUseError
from app.usecases.age_group import AgeGroupUseCase
from domain.age_group import AgeGroupOverlapError, DuplicateAgeGroupError
from infra.common.logging import LogAPIRoute
from infra.dependencies.age_groups import provide_use_case
from infra.schemas.age_group import AgeGroup as AgeGroupDTO
from infra.schemas.pagination import PageResult
from infra.utils.pagination import Pagination


class AgeGroupAPI:
    """API layer for age group operations."""
    
    TAGS = ["Age Groups"]
    PREFIX = "/age-groups"

    def __init__(
        self,
        app: FastAPI,
        *,
        dependencies: Sequence[params.Depends] | None = None,
    ) -> None:
        """Initialize API with FastAPI app and optional dependencies.
        
        Args:
            app: FastAPI application instance
            dependencies: Optional dependencies for all routes
        """
        self.router = APIRouter(
            dependencies=list(dependencies) if dependencies else None,
            route_class=LogAPIRoute,
        )
        self._register_routes()
        app.include_router(self.router, prefix=self.PREFIX, tags=list(self.TAGS))

    def _register_routes(self) -> None:
        """Register all age group API routes."""
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
        """List age groups with pagination.
        
        Retrieve a paginated list of all age groups in the system.
        Each age group contains name, minimum age, and maximum age information.
        
        Args:
            request: HTTP request object
            uc: Age group use case dependency
            page: Page number (default: 1)
            page_size: Number of items per page (default: 100)
            
        Returns:
            Paginated list of age groups
            
        Raises:
            HTTPException: If there's an error retrieving age groups
        """
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
        """Create new age group.
        
        Creates a new age group with the specified name and age range.
        Age ranges cannot overlap with existing groups.
        
        Args:
            group: Age group data to create
            uc: Age group use case dependency
            
        Returns:
            Created age group
            
        Raises:
            HTTPException: 409 if age group name already exists or age ranges overlap
            HTTPException: 422 if age range is invalid (min_age >= max_age)
        """
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
        """Delete age group by name.
        
        Removes an age group from the system. Cannot delete age groups
        that are currently in use by existing enrollments.
        
        Args:
            name: Name of age group to delete
            uc: Age group use case dependency
            
        Raises:
            HTTPException: 404 if age group not found
            HTTPException: 409 if age group is in use by enrollments
        """
        try:
            await uc.delete(name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except AgeGroupInUseError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
