from __future__ import annotations

from pydantic import BaseModel, Field

from infra.enumerators.enrollment import EnrollmentStatus


class EnrollmentAdmin(BaseModel):
    name: str
    age: int = Field(ge=0)
    cpf: str
    status: EnrollmentStatus
    requested_at: int | None = None
    enrolled_at: int | None = None
    age_group_name: str | None = None
