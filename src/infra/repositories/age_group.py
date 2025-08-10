from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tinydb.table import Table

from domain.age_group import AgeGroup, AgeRange
from infra.common.database import age_group_table
from infra.repositories.base import BaseRepository


class AgeGroupRepository(BaseRepository[AgeGroup]):
    """Repository for age group data operations."""

    def __init__(self, table: Table | None = None):
        """Initialize age group repository.
        
        Args:
            table: TinyDB table instance (default: from database config)
        """
        super().__init__(
            table=table or age_group_table,
            factory=self._to_domain,
            dumper=self._to_dict,
        )

    @staticmethod
    def _to_domain(data: Mapping[str, Any]) -> AgeGroup:
        """Convert database record to age group domain entity.
        
        Args:
            data: Database record data
            
        Returns:
            Age group domain entity
        """
        return AgeGroup(
            name=data["name"],
            age_range=AgeRange(data["min_age"], data["max_age"]),
        )

    @staticmethod
    def _to_dict(entity: AgeGroup) -> dict[str, Any]:
        """Convert age group domain entity to database record.
        
        Args:
            entity: Age group domain entity
            
        Returns:
            Database record dictionary
        """
        return {
            "name": entity.name,
            "min_age": entity.age_range.min_age,
            "max_age": entity.age_range.max_age,
        }

    def find_by_name(self, name: str) -> AgeGroup | None:
        """Find age group by name.
        
        Args:
            name: Age group name to search for
            
        Returns:
            Age group if found, None otherwise
        """
        return self.get_by_fields(name=name)

    def find_overlapping(self, *, min_age: int, max_age: int) -> list[AgeGroup]:
        """Find age groups with overlapping age ranges.
        
        Args:
            min_age: Minimum age of range to check
            max_age: Maximum age of range to check
            
        Returns:
            List of overlapping age groups
        """
        return self.search_by_fields(
            min_age__lte=max_age,
            max_age__gte=min_age,
        )

    def find_covering(self, age: int) -> AgeGroup | None:
        """Find age group that covers specific age.
        
        Args:
            age: Age to find coverage for
            
        Returns:
            Age group that covers the age, None if not found
        """
        return self.get_by_fields(min_age__lte=age, max_age__gte=age)
