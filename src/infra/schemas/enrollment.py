from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from infra.enumerators.enrollment import EnrollmentStatus


class EnrollmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=3, description="Full name.")
    age: Annotated[int, Field(ge=0, description="Age.")]
    cpf: str = Field(..., pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", description="CPF 999.999.999-99.")


class Enrollment(BaseModel):
    name: str
    age: int
    cpf: str
    status: EnrollmentStatus = Field(default=EnrollmentStatus.PENDING, description="Final status.")
