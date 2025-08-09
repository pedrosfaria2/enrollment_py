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
    TAGS = ["Enrollments"]
    PREFIX = "/enrollments"

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
        ent = await uc.status(cpf=cpf)
        if not ent:
            raise HTTPException(status_code=404, detail="enrollment not found")
        return EnrollmentDTO(name=ent.name, age=ent.age, cpf=ent.cpf, status=ent.status)
