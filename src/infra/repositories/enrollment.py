from infra.common.database import enrollment_table
from infra.repositories.base import BaseRepository
from infra.schemas.enrollment import Enrollment


class EnrollmentRepository(BaseRepository[Enrollment]):
    """
    Repository specifically for handling Enrollment data.
    """

    def __init__(self):
        super().__init__(table=enrollment_table, model=Enrollment)

    def find_by_cpf(self, cpf: str) -> Enrollment | None:
        return self.get_by_fields(cpf=cpf)
