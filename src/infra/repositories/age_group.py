from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tinydb.table import Table

from domain.age_group import AgeGroup, AgeRange
from infra.common.database import age_group_table
from infra.repositories.base import BaseRepository


class AgeGroupRepository(BaseRepository[AgeGroup]):
    """
    Repository specifically for handling AgeGroup data.
    """

    def __init__(self, table: Table | None = None):
        super().__init__(
            table=table or age_group_table,
            factory=self._to_domain,
            dumper=self._to_dict,
        )

    @staticmethod
    def _to_domain(data: Mapping[str, Any]) -> AgeGroup:
        return AgeGroup(
            name=data["name"],
            age_range=AgeRange(data["min_age"], data["max_age"]),
        )

    @staticmethod
    def _to_dict(entity: AgeGroup) -> dict[str, Any]:
        return {
            "name": entity.name,
            "min_age": entity.age_range.min_age,
            "max_age": entity.age_range.max_age,
        }

    def find_by_name(self, name: str) -> AgeGroup | None:
        return self.get_by_fields(name=name)

    def find_overlapping(self, *, min_age: int, max_age: int) -> list[AgeGroup]:
        return self.search_by_fields(
            min_age__lte=max_age,
            max_age__gte=min_age,
        )

    def find_covering(self, age: int) -> AgeGroup | None:
        return self.get_by_fields(min_age__lte=age, max_age__gte=age)
