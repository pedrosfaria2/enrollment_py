from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tinydb.table import Table

from domain.enrollment import Enrollment, EnrollmentStatus
from infra.common.database import enrollment_table
from infra.repositories.base import BaseRepository


class EnrollmentRepository(BaseRepository[Enrollment]):
    """Repository for enrollment data operations."""

    def __init__(self, table: Table | None = None):
        """Initialize enrollment repository.
        
        Args:
            table: TinyDB table instance (default: from database config)
        """
        super().__init__(
            table=table or enrollment_table,
            factory=self._to_domain,
            dumper=self._to_dict,
        )

    @staticmethod
    def _to_domain(data: Mapping[str, Any]) -> Enrollment:
        """Convert database record to enrollment domain entity.
        
        Args:
            data: Database record data
            
        Returns:
            Enrollment domain entity
        """
        return Enrollment(
            name=data["name"],
            age=data["age"],
            cpf=data["cpf"],
            status=EnrollmentStatus(data["status"]),
            requested_at=data.get("requested_at"),
            enrolled_at=data.get("enrolled_at"),
            age_group_name=data.get("age_group_name"),
        )

    @staticmethod
    def _to_dict(entity: Enrollment) -> dict[str, Any]:
        """Convert enrollment domain entity to database record.
        
        Args:
            entity: Enrollment domain entity
            
        Returns:
            Database record dictionary
        """
        return {
            "name": entity.name,
            "age": entity.age,
            "cpf": entity.cpf,
            "status": entity.status.value,
            "requested_at": entity.requested_at,
            "enrolled_at": entity.enrolled_at,
            "age_group_name": entity.age_group_name,
        }

    def find_by_cpf(self, cpf: str) -> Enrollment | None:
        """Find enrollment by CPF.
        
        Args:
            cpf: CPF to search for
            
        Returns:
            Enrollment if found, None otherwise
        """
        return self.get_by_fields(cpf=cpf)

    def exists_by_age_group(self, name: str, *, only_approved: bool = True) -> bool:
        """Check if enrollments exist for age group.
        
        Args:
            name: Age group name to check
            only_approved: Whether to check only approved enrollments (default: True)
            
        Returns:
            True if enrollments exist, False otherwise
        """
        fields: dict[str, Any] = {"age_group_name": name}
        if only_approved:
            fields["status"] = EnrollmentStatus.APPROVED.value
        return self.exists(**fields)
