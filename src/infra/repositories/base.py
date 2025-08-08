from functools import reduce

from pydantic import BaseModel
from tinydb import Query
from tinydb.queries import QueryInstance
from tinydb.table import Document, Table

from infra.common.database_lock import db_lock


class BaseRepository[ModelType: BaseModel]:
    """
    Generic repository for TinyDB.
    """

    def __init__(self, table: Table, model: type[ModelType]):
        """
        Initialize the repository with a TinyDB table and a Pydantic model.
        Args:
            table: The TinyDB table instance.
            model: The Pydantic model class for data validation and parsing.
        """
        self.table = table
        self.model = model
        self.Query = Query()

    def _to_model(self, document: Document | None) -> ModelType | None:
        """Converts a TinyDB Document into a Pydantic model instance."""
        if document:
            return self.model(**document)
        return None

    def _build_query(self, **kwargs) -> QueryInstance:
        """Builds a TinyDB Query object from keyword arguments."""
        query_list = [(getattr(self.Query, key) == value) for key, value in kwargs.items()]
        if not query_list:
            raise ValueError("Cannot build a query with no keyword arguments.")
        if len(query_list) == 1:
            return query_list[0]
        else:
            return reduce(lambda q1, q2: q1 & q2, query_list)

    def insert(self, entity: ModelType) -> ModelType:
        """Inserts a new entity into the database."""
        with db_lock:
            self.table.insert(entity.model_dump())
        return entity

    def get_by_id(self, doc_id: int) -> ModelType | None:
        """Retrieves an entity by its document ID."""
        doc = self.table.get(doc_id=doc_id)
        if isinstance(doc, dict):
            return self._to_model(doc)
        return None

    def get_by_fields(self, **kwargs) -> ModelType | None:
        """Retrieves the first entity that matches the given fields."""
        if not kwargs:
            return None
        query = self._build_query(**kwargs)
        doc = self.table.get(query)
        if isinstance(doc, dict):
            return self._to_model(doc)
        return None

    def get_all(self, offset: int = 0, limit: int = 100) -> list[ModelType]:
        """Retrieves all entities with pagination."""
        docs = self.table.all()
        paginated_docs = docs[offset : offset + limit]
        return [self.model(**doc) for doc in paginated_docs]

    def search_by_fields(self, offset: int = 0, limit: int = 100, **kwargs) -> list[ModelType]:
        """Retrieves all entities that match the given fields, with pagination."""
        if not kwargs:
            return self.get_all(offset=offset, limit=limit)

        query = self._build_query(**kwargs)
        docs = self.table.search(query)
        paginated_docs = docs[offset : offset + limit]
        return [self.model(**doc) for doc in paginated_docs]

    def update(self, data: dict, **kwargs) -> list[int]:
        """Updates entities matching the given fields."""
        with db_lock:
            return self.table.update(data, self._build_query(**kwargs))

    def remove(self, **kwargs) -> list[int]:
        """Removes entities matching the given fields."""
        with db_lock:
            return self.table.remove(self._build_query(**kwargs))

    def exists(self, **kwargs) -> bool:
        """Checks if an entity with the given fields exists."""
        query = self._build_query(**kwargs)
        return self.table.contains(query)

    def count(self, **kwargs) -> int:
        """Counts entities that match the given fields."""
        if not kwargs:
            return len(self.table)
        query = self._build_query(**kwargs)
        return self.table.count(query)
