from collections.abc import Callable, Mapping
from functools import reduce
from typing import Any, TypeVar

from tinydb import Query
from tinydb.queries import QueryInstance
from tinydb.table import Document, Table

from infra.common.database_lock import db_lock

T = TypeVar("T")


class BaseRepository[T]:
    """Generic repository for TinyDB operations.
    
    Provides common CRUD operations for domain entities using TinyDB storage.
    """

    def __init__(
        self, table: Table, *, factory: Callable[[Mapping[str, Any]], T], dumper: Callable[[T], dict[str, Any]]
    ):
        """Initialize repository with table and conversion functions.

        Args:
            table: TinyDB table instance
            factory: Function to convert database record to domain entity
            dumper: Function to convert domain entity to database record
        """
        self.table = table
        self._factory = factory
        self._dumper = dumper
        self.Query = Query()

    def _to_model(self, document: Document | None) -> T | None:
        """Convert TinyDB document to domain entity.
        
        Args:
            document: TinyDB document to convert
            
        Returns:
            Domain entity instance or None
        """
        if document:
            return self._factory(document)
        return None

    def _build_query(self, **kwargs) -> QueryInstance:
        """Build TinyDB query from keyword arguments.
        
        Args:
            **kwargs: Field filters with optional operators (field__op=value)
            
        Returns:
            TinyDB query instance
            
        Raises:
            ValueError: If no arguments provided or unsupported operator used
        """
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
        """Insert new entity into database.
        
        Args:
            entity: Domain entity to insert
            
        Returns:
            The inserted entity
        """
        with db_lock:
            self.table.insert(self._dumper(entity))
        return entity

    def get_by_id(self, doc_id: int) -> T | None:
        """Get entity by document ID.
        
        Args:
            doc_id: Document ID to search for
            
        Returns:
            Domain entity if found, None otherwise
        """
        doc = self.table.get(doc_id=doc_id)
        return self._to_model(doc) if isinstance(doc, dict) else None

    def get_by_fields(self, **kwargs) -> T | None:
        """Get first entity matching field criteria.
        
        Args:
            **kwargs: Field filters to match
            
        Returns:
            First matching entity or None
        """
        if not kwargs:
            return None
        query = self._build_query(**kwargs)
        doc = self.table.get(query)
        return self._to_model(doc) if isinstance(doc, dict) else None

    def get_all(self, offset: int = 0, limit: int = 100) -> list[T]:
        """Get all entities with pagination.
        
        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)
            
        Returns:
            List of domain entities
        """
        docs = self.table.all()
        paginated_docs = docs[offset : offset + limit]
        return [self._factory(doc) for doc in paginated_docs]

    def search_by_fields(self, offset: int = 0, limit: int = 100, **kwargs) -> list[T]:
        """Search entities by field criteria with pagination.
        
        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)
            **kwargs: Field filters to match
            
        Returns:
            List of matching domain entities
        """
        if not kwargs:
            return self.get_all(offset=offset, limit=limit)
        query = self._build_query(**kwargs)
        docs = self.table.search(query)
        paginated_docs = docs[offset : offset + limit]
        return [self._factory(doc) for doc in paginated_docs]

    def update(self, data: dict, **kwargs) -> list[int]:
        """Update entities matching field criteria.
        
        Args:
            data: Data to update
            **kwargs: Field filters to match entities for update
            
        Returns:
            List of updated document IDs
        """
        with db_lock:
            return self.table.update(data, self._build_query(**kwargs))

    def remove(self, **kwargs) -> list[int]:
        """Remove entities matching field criteria.
        
        Args:
            **kwargs: Field filters to match entities for removal
            
        Returns:
            List of removed document IDs
        """
        with db_lock:
            return self.table.remove(self._build_query(**kwargs))

    def exists(self, **kwargs) -> bool:
        """Check if entity exists matching field criteria.
        
        Args:
            **kwargs: Field filters to match
            
        Returns:
            True if entity exists, False otherwise
        """
        query = self._build_query(**kwargs)
        return self.table.contains(query)

    def count(self, **kwargs) -> int:
        """Count entities matching field criteria.
        
        Args:
            **kwargs: Field filters to match
            
        Returns:
            Number of matching entities
        """
        if not kwargs:
            return len(self.table)
        query = self._build_query(**kwargs)
        return self.table.count(query)
