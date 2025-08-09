from collections.abc import Callable, Mapping
from functools import reduce
from typing import Any, TypeVar

from tinydb import Query
from tinydb.queries import QueryInstance
from tinydb.table import Document, Table

from infra.common.database_lock import db_lock

T = TypeVar("T")


class BaseRepository[T]:
    """
    Generic repository for TinyDB.
    """

    def __init__(
        self, table: Table, *, factory: Callable[[Mapping[str, Any]], T], dumper: Callable[[T], dict[str, Any]]
    ):
        """
        Initialize the repository with a TinyDB table and a domain entity.

        Args:
            table: The TinyDB table instance.
            factory: Callable that converts a TinyDB record into a domain entity.
            dumper: Callable that converts a domain entity into a serialisable dict.
        """
        self.table = table
        self._factory = factory
        self._dumper = dumper
        self.Query = Query()

    def _to_model(self, document: Document | None) -> T | None:
        """Converts a TinyDB Document into a domain entity instance."""
        if document:
            return self._factory(document)
        return None

    def _build_query(self, **kwargs) -> QueryInstance:
        """Builds a TinyDB Query object from keyword arguments."""
        if not kwargs:
            raise ValueError("Cannot build a query with no keyword arguments.")

        def _one(key, value):  # noqa: PLR0911
            if "__" not in key:
                return getattr(self.Query, key) == value
            field, op = key.split("__", 1)
            qf = getattr(self.Query, field)
            match op:
                case "lt":
                    return qf < value
                case "lte":
                    return qf <= value
                case "gt":
                    return qf > value
                case "gte":
                    return qf >= value
                case "ne":
                    return qf != value
                case "in":
                    return qf.one_of(value)
                case "nin":
                    return ~qf.one_of(value)
                case _:
                    raise ValueError(f"Unsupported operator: {op}")

        queries = [_one(k, v) for k, v in kwargs.items()]
        return queries[0] if len(queries) == 1 else reduce(lambda a, b: a & b, queries)

    def insert(self, entity: T) -> T:
        """Inserts a new entity into the database."""
        with db_lock:
            self.table.insert(self._dumper(entity))
        return entity

    def get_by_id(self, doc_id: int) -> T | None:
        """Retrieves an entity by its document ID."""
        doc = self.table.get(doc_id=doc_id)
        return self._to_model(doc) if isinstance(doc, dict) else None

    def get_by_fields(self, **kwargs) -> T | None:
        """Retrieves the first entity that matches the given fields."""
        if not kwargs:
            return None
        query = self._build_query(**kwargs)
        doc = self.table.get(query)
        return self._to_model(doc) if isinstance(doc, dict) else None

    def get_all(self, offset: int = 0, limit: int = 100) -> list[T]:
        """Retrieves all entities with pagination."""
        docs = self.table.all()
        paginated_docs = docs[offset : offset + limit]
        return [self._factory(doc) for doc in paginated_docs]

    def search_by_fields(self, offset: int = 0, limit: int = 100, **kwargs) -> list[T]:
        """Retrieves all entities that match the given fields, with pagination."""
        if not kwargs:
            return self.get_all(offset=offset, limit=limit)
        query = self._build_query(**kwargs)
        docs = self.table.search(query)
        paginated_docs = docs[offset : offset + limit]
        return [self._factory(doc) for doc in paginated_docs]

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
