from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path, params, status

from app.usecases.enrollment import EnrollmentUseCase
from infra.common.logging import LogAPIRoute
from infra.dependencies.enrollment import provide_use_case
from infra.schemas.enrollment import Enrollment as EnrollmentDTO
from infra.schemas.enrollment import EnrollmentCreate


class EnrollmentAPI:
    """API layer for enrollment operations."""

    TAGS = ["Enrollments"]
    PREFIX = "/enrollments"

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
        """Register all enrollment API routes."""
        self.router.add_api_route(
            "/",
            self.request_enrollment,
            methods=["POST"],
            status_code=status.HTTP_202_ACCEPTED,
            response_model=None,
            summary="Request enrollment (enqueue for processing)",
        )
        self.router.add_api_route(
            "/{cpf}",
            self.get_status,
            methods=["GET"],
            response_model=EnrollmentDTO,
            summary="Get enrollment status by CPF",
        )

    async def request_enrollment(
        self,
        dto: EnrollmentCreate,
        uc: Annotated[EnrollmentUseCase, Depends(provide_use_case)],
    ) -> None:
        """Request enrollment processing.

        Submits a new enrollment request for processing. The request is validated
        for age group coverage and duplicate CPF checking before being queued.

        Args:
            dto: Enrollment creation data
            uc: Enrollment use case dependency

        Raises:
            HTTPException: 422 if no age group covers the specified age
            HTTPException: 409 if enrollment already approved for this CPF
            HTTPException: 503 if enrollment service is unavailable
        """
        try:
            await uc.request(name=dto.name, age=dto.age, cpf=dto.cpf)
            return None
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail="service unavailable") from exc

    async def get_status(
        self,
        cpf: Annotated[str, Path(pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")],
        uc: Annotated[EnrollmentUseCase, Depends(provide_use_case)],
    ) -> EnrollmentDTO:
        """Get enrollment status by CPF.

        Retrieves the current enrollment status for a given CPF.
        CPF must be in the format XXX.XXX.XXX-XX.

        Args:
            cpf: CPF to search for (format: XXX.XXX.XXX-XX)
            uc: Enrollment use case dependency

        Returns:
            Enrollment data with current status

        Raises:
            HTTPException: 404 if enrollment not found for the given CPF
        """
        ent = await uc.status(cpf=cpf)
        if not ent:
            raise HTTPException(status_code=404, detail="enrollment not found")
        return EnrollmentDTO(name=ent.name, age=ent.age, cpf=ent.cpf, status=ent.status)
