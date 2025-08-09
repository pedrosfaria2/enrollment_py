from __future__ import annotations

from dataclasses import dataclass


class AgeGroupError(Exception): ...


class DuplicateAgeGroupError(AgeGroupError):
    def __init__(self, msg: str = "Age group name already exists."):
        super().__init__(msg)


class AgeGroupOverlapError(AgeGroupError):
    def __init__(self, msg: str = "Age range overlaps an existing group."):
        super().__init__(msg)


class AgeGroupInUseError(AgeGroupError):
    def __init__(self, msg: str = "Age group is in use and cannot be deleted."):
        super().__init__(msg)


@dataclass(frozen=True, slots=True)
class AgeRange:
    min_age: int
    max_age: int

    def __post_init__(self):
        if self.min_age > self.max_age:
            raise ValueError("min_age must be ≤ max_age")

    def overlaps(self, other: AgeRange) -> bool:
        return self.min_age <= other.max_age and other.min_age <= self.max_age


@dataclass(slots=True)
class AgeGroup:
    name: str
    age_range: AgeRange

    @staticmethod
    def create(
        name: str,
        min_age: int,
        max_age: int,
        existing: list[AgeGroup],
    ) -> AgeGroup:
        if any(g.name == name for g in existing):
            raise DuplicateAgeGroupError
        new_range = AgeRange(min_age, max_age)
        if any(new_range.overlaps(g.age_range) for g in existing):
            raise AgeGroupOverlapError
        return AgeGroup(name=name, age_range=new_range)
