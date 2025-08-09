from dataclasses import dataclass

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from infra.repositories.base import BaseRepository


@dataclass
class Row:
    name: str
    age: int
    tags: list[str]


def _factory(d: dict) -> Row:
    return Row(name=d["name"], age=d["age"], tags=d["tags"])


def _dumper(r: Row) -> dict:
    return {"name": r.name, "age": r.age, "tags": r.tags}


@pytest.fixture
def table():
    db = TinyDB(storage=MemoryStorage)
    return db.table("rows")


@pytest.fixture
def repo(table) -> BaseRepository[Row]:
    return BaseRepository(table=table, factory=_factory, dumper=_dumper)  # type: ignore


def seed(repo: BaseRepository[Row]):
    repo.insert(Row("alice", 20, ["a", "b"]))
    repo.insert(Row("bob", 30, ["b"]))
    repo.insert(Row("carol", 40, ["c"]))
    repo.insert(Row("dave", 30, ["a", "c"]))


def test_insert_and_get_by_id(repo, table):
    doc_id = table.insert(_dumper(Row("eve", 22, ["x"])))
    r = repo.get_by_id(doc_id)
    assert r and r.name == "eve" and r.age == 22 and r.tags == ["x"]


def test_get_by_fields_equality(repo):
    seed(repo)
    r = repo.get_by_fields(name="bob")
    assert r and r.age == 30


def test_exists_requires_filter_raises(repo):
    with pytest.raises(ValueError, match="Cannot build a query"):
        repo.exists()  # no kwargs


def test_exists_and_count(repo):
    seed(repo)
    assert repo.exists(name="alice") is True
    assert repo.exists(name="unknown") is False
    assert repo.count() == 4
    assert repo.count(age=30) == 2


def test_get_all_pagination(repo):
    seed(repo)
    rows = repo.get_all(offset=1, limit=2)
    assert [r.name for r in rows] == ["bob", "carol"]


def test_search_by_fields_with_operators(repo):
    seed(repo)
    gt = repo.search_by_fields(age__gt=20)
    assert sorted(r.name for r in gt) == ["bob", "carol", "dave"]

    gte = repo.search_by_fields(age__gte=30)
    assert sorted(r.name for r in gte) == ["bob", "carol", "dave"]

    lt = repo.search_by_fields(age__lt=30)
    assert [r.name for r in lt] == ["alice"]

    lte = repo.search_by_fields(age__lte=30)
    assert sorted(r.name for r in lte) == ["alice", "bob", "dave"]

    ne = repo.search_by_fields(age__ne=30)
    assert sorted(r.name for r in ne) == ["alice", "carol"]

    inq = repo.search_by_fields(name__in=["alice", "carol", "zzz"])
    assert sorted(r.name for r in inq) == ["alice", "carol"]

    nin = repo.search_by_fields(name__nin=["bob", "dave"])
    assert sorted(r.name for r in nin) == ["alice", "carol"]


def test_update_by_field(repo):
    seed(repo)
    updated_ids = repo.update({"age": 31}, name="bob")
    assert len(updated_ids) == 1
    r = repo.get_by_fields(name="bob")
    assert r and r.age == 31


def test_remove_by_field(repo):
    seed(repo)
    removed_ids = repo.remove(name="carol")
    assert len(removed_ids) == 1
    assert repo.exists(name="carol") is False
