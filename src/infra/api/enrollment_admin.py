from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, params

from app.usecases.enrollment_admin import EnrollmentAdminUseCase
from domain.enrollment import Enrollment
from infra.common.logging import LogAPIRoute
from infra.dependencies.enrollment_admin import provide_admin_use_case
from infra.enumerators.enrollment import EnrollmentStatus
from infra.schemas.enrollment_admin import EnrollmentAdmin as EnrollmentDTO
from infra.schemas.pagination import PageResult
from infra.utils.pagination import Pagination


class EnrollmentAdminAPI:
    """API layer for enrollment admin operations."""
    
    TAGS = ["Enrollments Admin"]
    PREFIX = "/enrollments/admin"

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
        """Register all enrollment admin API routes."""
        self.router.add_api_route(
            "/all",
            self.get_all,
            methods=["GET"],
            response_model=PageResult[EnrollmentDTO],
            summary="List all enrollments",
        )
        self.router.add_api_route(
            "/by-cpf/{cpf}",
            self.get_by_cpf,
            methods=["GET"],
            response_model=EnrollmentDTO,
            summary="Get enrollment by CPF",
        )
        self.router.add_api_route(
            "/by-group/{name}",
            self.list_by_age_group,
            methods=["GET"],
            response_model=PageResult[EnrollmentDTO],
            summary="List enrollments by age group",
        )
        self.router.add_api_route(
            "/by-name",
            self.list_by_name,
            methods=["GET"],
            response_model=PageResult[EnrollmentDTO],
            summary="List enrollments by name",
        )
        self.router.add_api_route(
            "/by-status",
            self.list_by_status,
            methods=["GET"],
            response_model=PageResult[EnrollmentDTO],
            summary="List enrollments by status",
        )

    @staticmethod
    def _to_dto(e: Enrollment) -> EnrollmentDTO:
        """Convert domain enrollment to DTO.
        
        Args:
            e: Domain enrollment object
            
        Returns:
            Enrollment DTO
        """
        return EnrollmentDTO(
            name=e.name,
            age=e.age,
            cpf=e.cpf,
            status=e.status,
            requested_at=e.requested_at,
            enrolled_at=e.enrolled_at,
            age_group_name=e.age_group_name,
        )

    async def get_all(
        self,
        request: Request,
        uc: Annotated[EnrollmentAdminUseCase, Depends(provide_admin_use_case)],
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(gt=0)] = 100,
    ) -> PageResult[EnrollmentDTO]:
        """Get all enrollments with pagination.
        
        Retrieves a paginated list of all enrollments in the system,
        including their status, timestamps, and age group information.
        
        Args:
            request: HTTP request object
            uc: Enrollment admin use case dependency
            page: Page number (default: 1)
            page_size: Number of items per page (default: 100)
            
        Returns:
            Paginated list of all enrollments
        """
        offset = (page - 1) * page_size
        total = await uc.count_all()
        items = await uc.get_all(offset=offset, limit=page_size)
        dto_items = [self._to_dto(x) for x in items]
        return Pagination[EnrollmentDTO].create(
            request=request,
            items=dto_items,
            total_items=total,
            page=page,
            page_size=page_size,
            schema_class=EnrollmentDTO,
        )

    async def get_by_cpf(
        self,
        cpf: str,
        uc: Annotated[EnrollmentAdminUseCase, Depends(provide_admin_use_case)],
    ) -> EnrollmentDTO:
        """Get enrollment by CPF.
        
        Retrieves detailed enrollment information for a specific CPF,
        including all status history and timestamps.
        
        Args:
            cpf: CPF to search for
            uc: Enrollment admin use case dependency
            
        Returns:
            Enrollment data with full details
            
        Raises:
            HTTPException: 404 if enrollment not found for the given CPF
        """
        e = await uc.get_by_cpf(cpf=cpf)
        if not e:
            raise HTTPException(status_code=404, detail="enrollment not found")
        return self._to_dto(e)

    async def list_by_age_group(
        self,
        request: Request,
        name: str,
        uc: Annotated[EnrollmentAdminUseCase, Depends(provide_admin_use_case)],
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(gt=0)] = 100,
    ) -> PageResult[EnrollmentDTO]:
        """List enrollments by age group with pagination.
        
        Retrieves all enrollments that belong to a specific age group,
        useful for analyzing enrollment distribution across age ranges.
        
        Args:
            request: HTTP request object
            name: Age group name to filter by
            uc: Enrollment admin use case dependency
            page: Page number (default: 1)
            page_size: Number of items per page (default: 100)
            
        Returns:
            Paginated list of enrollments in the age group
        """
        offset = (page - 1) * page_size
        total = await uc.count_by_age_group(name=name)
        items = await uc.list_by_age_group(name=name, offset=offset, limit=page_size)
        dto_items = [self._to_dto(x) for x in items]
        return Pagination[EnrollmentDTO].create(
            request=request,
            items=dto_items,
            total_items=total,
            page=page,
            page_size=page_size,
            schema_class=EnrollmentDTO,
        )

    async def list_by_name(
        self,
        request: Request,
        name: Annotated[str, Query(min_length=1)],
        uc: Annotated[EnrollmentAdminUseCase, Depends(provide_admin_use_case)],
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(gt=0)] = 100,
    ) -> PageResult[EnrollmentDTO]:
        """List enrollments by student name with pagination.
        
        Searches for enrollments by student name. Useful for finding
        all enrollments for students with similar names.
        
        Args:
            request: HTTP request object
            name: Student name to filter by (minimum 1 character)
            uc: Enrollment admin use case dependency
            page: Page number (default: 1)
            page_size: Number of items per page (default: 100)
            
        Returns:
            Paginated list of enrollments matching the name
        """
        offset = (page - 1) * page_size
        total = await uc.count_by_name(name=name)
        items = await uc.list_by_name(name=name, offset=offset, limit=page_size)
        dto_items = [self._to_dto(x) for x in items]
        return Pagination[EnrollmentDTO].create(
            request=request,
            items=dto_items,
            total_items=total,
            page=page,
            page_size=page_size,
            schema_class=EnrollmentDTO,
        )

    async def list_by_status(
        self,
        request: Request,
        status_: Annotated[Literal["APPROVED", "REJECTED"], Query(alias="status")],
        uc: Annotated[EnrollmentAdminUseCase, Depends(provide_admin_use_case)],
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(gt=0)] = 100,
    ) -> PageResult[EnrollmentDTO]:
        """List enrollments by status with pagination.
        
        Filters enrollments by their current status. Useful for administrative
        tasks like reviewing approved or rejected enrollments.
        
        Args:
            request: HTTP request object
            status_: Enrollment status to filter by (APPROVED or REJECTED)
            uc: Enrollment admin use case dependency
            page: Page number (default: 1)
            page_size: Number of items per page (default: 100)
            
        Returns:
            Paginated list of enrollments with the specified status
        """
        offset = (page - 1) * page_size
        status_enum = EnrollmentStatus(status_)
        total = await uc.count_by_status(status=status_enum)
        items = await uc.list_by_status(status=status_enum, offset=offset, limit=page_size)
        return Pagination[EnrollmentDTO].create(
            request=request,
            items=[
                EnrollmentDTO(
                    name=i.name,
                    age=i.age,
                    cpf=i.cpf,
                    status=i.status,
                    requested_at=i.requested_at,
                    enrolled_at=i.enrolled_at,
                    age_group_name=i.age_group_name,
                )
                for i in items
            ],
            total_items=total,
            page=page,
            page_size=page_size,
            schema_class=EnrollmentDTO,
        )
