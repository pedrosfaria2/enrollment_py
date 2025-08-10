from __future__ import annotations

from dataclasses import dataclass


class AgeGroupError(Exception):
    """Base exception for age group related errors."""
    ...


class DuplicateAgeGroupError(AgeGroupError):
    """Raised when attempting to create an age group with a name that already exists."""
    
    def __init__(self, msg: str = "Age group name already exists."):
        super().__init__(msg)


class AgeGroupOverlapError(AgeGroupError):
    """Raised when an age group's range overlaps with an existing age group."""
    
    def __init__(self, msg: str = "Age range overlaps an existing group."):
        super().__init__(msg)


class AgeGroupInUseError(AgeGroupError):
    """Raised when attempting to delete an age group that is currently in use."""
    
    def __init__(self, msg: str = "Age group is in use and cannot be deleted."):
        super().__init__(msg)


@dataclass(frozen=True, slots=True)
class AgeRange:
    """Age range with inclusive min/max boundaries and overlap detection."""
    min_age: int
    max_age: int

    def __post_init__(self):
        """Validate that min_age is not greater than max_age."""
        if self.min_age > self.max_age:
            raise ValueError("min_age must be ≤ max_age")

    def overlaps(self, other: AgeRange) -> bool:
        """Check if ranges overlap using inclusive boundaries."""
        return self.min_age <= other.max_age and other.min_age <= self.max_age


@dataclass(slots=True)
class AgeGroup:
    """Named age group with unique name and non-overlapping age range."""
    name: str
    age_range: AgeRange

    @staticmethod
    def create(
        name: str,
        min_age: int,
        max_age: int,
        existing: list[AgeGroup],
    ) -> AgeGroup:
        """Create validated age group with unique name and non-overlapping range."""
        if any(g.name == name for g in existing):
            raise DuplicateAgeGroupError
        new_range = AgeRange(min_age, max_age)
        if any(new_range.overlaps(g.age_range) for g in existing):
            raise AgeGroupOverlapError
        return AgeGroup(name=name, age_range=new_range)
