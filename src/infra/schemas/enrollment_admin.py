from __future__ import annotations

from pydantic import BaseModel, Field

from infra.enumerators.enrollment import EnrollmentStatus


class EnrollmentAdmin(BaseModel):
    name: str = Field(description="Student's full name")
    age: int = Field(ge=0, description="Student's age in years")
    cpf: str = Field(description="Brazilian CPF document number")
    status: EnrollmentStatus = Field(description="Current enrollment status (PENDING, APPROVED, REJECTED)")
    requested_at: int | None = Field(None, description="Unix timestamp when enrollment was requested")
    enrolled_at: int | None = Field(None, description="Unix timestamp when enrollment was processed")
    age_group_name: str | None = Field(None, description="Name of the age group this enrollment belongs to")
