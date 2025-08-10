from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from infra.enumerators.enrollment import EnrollmentStatus


class EnrollmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=3, description="Student's full name (minimum 3 characters)")
    age: Annotated[int, Field(ge=0, description="Student's age in years (must be non-negative)")]
    cpf: str = Field(..., pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", description="Brazilian CPF in format XXX.XXX.XXX-XX")


class Enrollment(BaseModel):
    name: str = Field(description="Student's full name")
    age: int = Field(description="Student's age in years")
    cpf: str = Field(description="Brazilian CPF document number")
    status: EnrollmentStatus = Field(
        default=EnrollmentStatus.PENDING, description="Current enrollment status (PENDING, APPROVED, REJECTED)"
    )
