from typing import Annotated

from pydantic import BaseModel, Field

from infra.enumerators.enrollment import EnrollmentStatus


class Enrollment(BaseModel):
    name: str = Field(..., min_length=3, description="The full name of the person enrolling.")
    age: Annotated[int, Field(ge=0, description="The age of the person.")]
    cpf: str = Field(..., pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", description="The CPF in the format 123.456.789-00.")
    status: EnrollmentStatus = Field(
        default=EnrollmentStatus.PENDING, description="The current status of the enrollment."
    )
