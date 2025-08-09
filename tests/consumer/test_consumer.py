from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from infra.enumerators.enrollment import EnrollmentStatus
from worker import consumer


def test_digits_only():
    assert consumer._digits_only("154.839.318-58") == "15483931858"
    assert consumer._digits_only("abc123") == "123"
    assert consumer._digits_only("") == ""


@pytest.mark.parametrize(
    "cpf, ok",
    [
        ("529.982.247-25", True),  # valid sample CPF
        ("111.111.111-11", False),  # repeated digits invalid
        ("154.839.318-58", True),  # valid (matches your earlier payload)
        ("123.456.789-00", False),  # invalid check digits
    ],
)
def test_cpf_valid(cpf, ok):
    assert consumer._cpf_valid(cpf) is ok


@dataclass
class FakeEnrollment:
    name: str
    age: int
    cpf: str
    status: EnrollmentStatus
    requested_at: int | None
    enrolled_at: int | None
    age_group_name: str | None


class FakeEnrollmentRepo:
    def __init__(self, existing_by_cpf: dict[str, FakeEnrollment] | None = None):
        self.store: dict[str, FakeEnrollment] = dict(existing_by_cpf or {})
        self.updated = []
        self.inserted = []

    def find_by_cpf(self, cpf: str):
        ent = self.store.get(cpf)
        return (
            None
            if ent is None
            else consumer.Enrollment(
                name=ent.name,
                age=ent.age,
                cpf=ent.cpf,
                status=ent.status,
                requested_at=ent.requested_at,
                enrolled_at=ent.enrolled_at,
                age_group_name=ent.age_group_name,
            )
        )

    def update(self, data: dict, **kwargs) -> list[int]:
        cpf = kwargs["cpf"]
        if cpf in self.store:
            self.updated.append((cpf, data))
            self.store[cpf] = FakeEnrollment(
                name=data["name"],
                age=data["age"],
                cpf=data["cpf"],
                status=EnrollmentStatus(data["status"]),
                requested_at=data["requested_at"],
                enrolled_at=data["enrolled_at"],
                age_group_name=data["age_group_name"],
            )
            return [1]
        return []

    def insert(self, entity):
        self.inserted.append(entity)
        self.store[entity.cpf] = FakeEnrollment(
            name=entity.name,
            age=entity.age,
            cpf=entity.cpf,
            status=entity.status,
            requested_at=entity.requested_at,
            enrolled_at=entity.enrolled_at,
            age_group_name=entity.age_group_name,
        )
        return entity


class FakeAgeGroupRepo:
    def __init__(self, names: set[str]):
        self.names = set(names)

    def exists(self, **kwargs) -> bool:
        return kwargs.get("name") in self.names


class FakeChannel:
    def __init__(self):
        self.acks: list[int] = []
        self.nacks: list[tuple[int, bool]] = []

    def basic_ack(self, *, delivery_tag: int):
        self.acks.append(delivery_tag)

    def basic_nack(self, *, delivery_tag: int, requeue: bool):
        self.nacks.append((delivery_tag, requeue))


@dataclass
class FakeMethod:
    delivery_tag: int


def make_payload(**overrides: Any) -> dict[str, Any]:
    base = {
        "name": "Alice",
        "age": 10,
        "cpf": "529.982.247-25",
        "requested_at": 1_700_000_000,
        "age_group_name": "kids",
    }
    base.update(overrides)
    return base


def test_upsert_final_approved_insert(monkeypatch):
    repo = FakeEnrollmentRepo()
    groups = FakeAgeGroupRepo({"kids"})

    monkeypatch.setattr(consumer, "EnrollmentRepository", lambda: repo)
    monkeypatch.setattr(consumer, "AgeGroupRepository", lambda: groups)

    payload = make_payload()
    consumer._upsert_final(repo, groups, payload)  # type: ignore
    ent = repo.store[payload["cpf"]]
    assert ent.status == EnrollmentStatus.APPROVED
    assert ent.age_group_name == "kids"
    assert ent.enrolled_at is not None


def test_upsert_final_rejected_no_group(monkeypatch):
    repo = FakeEnrollmentRepo()
    groups = FakeAgeGroupRepo(set())

    consumer._upsert_final(repo, groups, make_payload())  # type: ignore
    ent = repo.store["529.982.247-25"]
    assert ent.status == EnrollmentStatus.REJECTED
    assert ent.age_group_name is None
    assert ent.enrolled_at is None


def test_upsert_final_rejected_bad_cpf(monkeypatch):
    repo = FakeEnrollmentRepo()
    groups = FakeAgeGroupRepo({"kids"})

    payload = make_payload(cpf="123.456.789-00")
    consumer._upsert_final(repo, groups, payload)  # type: ignore
    ent = repo.store[payload["cpf"]]
    assert ent.status == EnrollmentStatus.REJECTED
    assert ent.enrolled_at is None


def test_upsert_final_existing_approved_is_noop(monkeypatch):
    cpf = "529.982.247-25"
    existing = FakeEnrollment(
        name="Alice",
        age=10,
        cpf=cpf,
        status=EnrollmentStatus.APPROVED,
        requested_at=1_700_000_000,
        enrolled_at=1_700_000_100,
        age_group_name="kids",
    )
    repo = FakeEnrollmentRepo({cpf: existing})
    groups = FakeAgeGroupRepo({"kids"})

    consumer._upsert_final(repo, groups, make_payload(cpf=cpf))  # type: ignore
    assert repo.updated == []
    assert repo.inserted == []


def test_upsert_final_existing_rejected_gets_replaced(monkeypatch):
    cpf = "529.982.247-25"
    existing = FakeEnrollment(
        name="Alice",
        age=10,
        cpf=cpf,
        status=EnrollmentStatus.REJECTED,
        requested_at=1_700_000_000,
        enrolled_at=None,
        age_group_name=None,
    )
    repo = FakeEnrollmentRepo({cpf: existing})
    groups = FakeAgeGroupRepo({"kids"})

    consumer._upsert_final(repo, groups, make_payload(cpf=cpf))  # type: ignore
    assert repo.updated
    assert repo.store[cpf].status in {EnrollmentStatus.APPROVED, EnrollmentStatus.REJECTED}


def test_on_message_success_acks(monkeypatch):
    repo = FakeEnrollmentRepo()
    groups = FakeAgeGroupRepo({"kids"})
    monkeypatch.setattr(consumer, "EnrollmentRepository", lambda: repo)
    monkeypatch.setattr(consumer, "AgeGroupRepository", lambda: groups)
    monkeypatch.setattr(consumer.time, "sleep", lambda *_: None)
    monkeypatch.setenv("ENROLLMENT_WORKER_MIN_SECONDS", "0")

    ch = FakeChannel()
    method = FakeMethod(delivery_tag=7)
    props = object()
    body = json.dumps(make_payload()).encode()

    consumer._on_message(ch, method, props, body)  # type: ignore
    assert ch.acks == [7]
    assert ch.nacks == []


def test_on_message_exception_nacks(monkeypatch):
    monkeypatch.setattr(consumer, "EnrollmentRepository", lambda: FakeEnrollmentRepo())
    monkeypatch.setattr(consumer, "AgeGroupRepository", lambda: FakeAgeGroupRepo(set()))
    monkeypatch.setattr(consumer.time, "sleep", lambda *_: None)
    monkeypatch.setenv("ENROLLMENT_WORKER_MIN_SECONDS", "0")

    ch = FakeChannel()
    method = FakeMethod(delivery_tag=9)
    props = object()

    def bad_loads(_):
        raise ValueError("boom")

    monkeypatch.setattr(consumer.json, "loads", bad_loads)

    consumer._on_message(ch, method, props, b"{}")  # type: ignore
    assert ch.acks == []
    assert ch.nacks == [(9, True)]
