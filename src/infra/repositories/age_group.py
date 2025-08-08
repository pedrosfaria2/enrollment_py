from tinydb.table import Table

from infra.common.database import age_group_table
from infra.repositories.base import BaseRepository
from infra.schemas.age_group import AgeGroup


class AgeGroupRepository(BaseRepository[AgeGroup]):
    """
    Repository specifically for handling AgeGroup data.
    """

    def __init__(self, table: Table | None = None):
        super().__init__(table=table or age_group_table, model=AgeGroup)

    def find_by_name(self, name: str) -> AgeGroup | None:
        return self.get_by_fields(name=name)
