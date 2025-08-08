from tinydb.table import Table

from infra.common.database import enrollment_table
from infra.repositories.base import BaseRepository
from infra.schemas.enrollment import Enrollment


class EnrollmentRepository(BaseRepository[Enrollment]):
    """
    Repository specifically for handling Enrollment data.
    """

    def __init__(self, table: Table | None = None):
        super().__init__(table=table or enrollment_table, model=Enrollment)

    def find_by_cpf(self, cpf: str) -> Enrollment | None:
        return self.get_by_fields(cpf=cpf)
