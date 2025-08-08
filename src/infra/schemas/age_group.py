from typing import Annotated, Self

from pydantic import BaseModel, Field, model_validator


class AgeGroup(BaseModel):
    name: str = Field(..., description="Name of the age group")
    min_age: Annotated[int, Field(ge=0, description="Minimum age for the group")]
    max_age: Annotated[int, Field(ge=0, description="Maximum age for the group")]

    @model_validator(mode="after")
    def check_ages(self) -> Self:
        if self.min_age > self.max_age:
            raise ValueError("Minimum age cannot be greater than maximum age.")
        return self
