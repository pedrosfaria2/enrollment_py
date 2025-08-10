from typing import Annotated, Self

from pydantic import BaseModel, Field, model_validator


class AgeGroup(BaseModel):
    name: str = Field(..., description="Unique name identifier for the age group")
    min_age: Annotated[int, Field(ge=0, description="Minimum age (inclusive) for students in this group")]
    max_age: Annotated[int, Field(ge=0, description="Maximum age (inclusive) for students in this group")]

    @model_validator(mode="after")
    def check_ages(self) -> Self:
        if self.min_age > self.max_age:
            raise ValueError("Minimum age cannot be greater than maximum age.")
        return self
