from __future__ import annotations

import time
from collections.abc import Callable

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.services.enrollment import EnrollmentService
from app.usecases.enrollment import EnrollmentUseCase
from domain.age_group import AgeGroup, AgeRange
from domain.enrollment import Enrollment, EnrollmentStatus
from infra.api.enrollment import EnrollmentAPI
from infra.dependencies.enrollment import provide_use_case
from infra.repositories.age_group import AgeGroupRepository
from infra.repositories.enrollment import EnrollmentRepository


class _StubPublisher:
    def __init__(self) -> None:
        self.messages: list[dict] = []
        self.fail: bool = False

    def publish(self, payload: dict) -> None:
        if self.fail:
            raise RuntimeError("publish failed (stub)")
        self.messages.append(payload)


@pytest.fixture
def app_client(
    tmp_db,
) -> tuple[TestClient, Callable[[], None], AgeGroupRepository, EnrollmentRepository, _StubPublisher]:
    age_table = tmp_db.table("age_groups")
    enr_table = tmp_db.table("enrollments")

    age_repo = AgeGroupRepository(table=age_table)
    enr_repo = EnrollmentRepository(table=enr_table)

    pub = _StubPublisher()
    svc = EnrollmentService(age_groups=age_repo, enrollments=enr_repo)
    uc = EnrollmentUseCase(service=svc, publisher=pub)

    app = FastAPI()
    EnrollmentAPI(app)
    app.dependency_overrides[provide_use_case] = lambda: uc

    client = TestClient(app)

    def _reset() -> None:
        age_table.truncate()
        enr_table.truncate()
        pub.messages.clear()

    _reset()
    return client, _reset, age_repo, enr_repo, pub


def test_post_202_enqueues_when_ok(app_client):
    client, reset, age_repo, _enr_repo, pub = app_client
    reset()
    age_group = AgeGroup(name="KIDS", age_range=AgeRange(5, 12))
    age_repo.insert(age_group)

    payload = {"name": "Alice", "age": 11, "cpf": "441.354.448-06"}
    r = client.post("/enrollments/", json=payload)
    assert r.status_code == 202

    assert len(pub.messages) == 1
    msg = pub.messages[0]
    assert msg["name"] == "Alice"
    assert msg["age"] == 11
    assert msg["cpf"] == "441.354.448-06"
    assert msg["age_group_name"] == "KIDS"
    assert msg["status"] == "PENDING"
    assert isinstance(msg["requested_at"], int)


def test_post_422_when_no_covering_group(app_client):
    client, reset, _age_repo, _enr_repo, pub = app_client
    reset()

    r = client.post("/enrollments/", json={"name": "Bob", "age": 99, "cpf": "123.456.789-00"})
    assert r.status_code == 422
    assert r.json()["detail"]
    assert pub.messages == []


def test_post_409_when_already_approved(app_client):
    client, reset, age_repo, enr_repo, pub = app_client
    reset()
    age_group = AgeGroup(name="ADULT", age_range=AgeRange(18, 60))
    age_repo.insert(age_group)

    approved = Enrollment(
        name="Carol",
        age=30,
        cpf="111.222.333-44",
        status=EnrollmentStatus.APPROVED,
        requested_at=int(time.time()) - 10,
        enrolled_at=int(time.time()),
        age_group_name="ADULT",
    )
    enr_repo.insert(approved)

    r = client.post("/enrollments/", json={"name": "Carol", "age": 30, "cpf": "111.222.333-44"})
    assert r.status_code == 409
    assert "already approved" in r.json()["detail"].lower()
    assert pub.messages == []


def test_get_status_404_when_absent(app_client):
    client, reset, _age_repo, _enr_repo, _pub = app_client
    reset()
    r = client.get("/enrollments/000.000.000-00")
    assert r.status_code == 404


def test_get_status_200_when_present(app_client):
    client, reset, age_repo, enr_repo, _pub = app_client
    reset()
    age_group = AgeGroup(name="YOUTH", age_range=AgeRange(13, 17))
    age_repo.insert(age_group)
    ent = Enrollment(
        name="Dave",
        age=15,
        cpf="555.666.777-88",
        status=EnrollmentStatus.REJECTED,
        requested_at=int(time.time()) - 50,
        enrolled_at=None,
        age_group_name="YOUTH",
    )
    enr_repo.insert(ent)

    r = client.get("/enrollments/555.666.777-88")
    assert r.status_code == 200
    body = r.json()
    assert body == {"name": "Dave", "age": 15, "cpf": "555.666.777-88", "status": "REJECTED"}


def test_post_503_when_publisher_fails(app_client):
    client, reset, age_repo, _enr_repo, pub = app_client
    reset()
    age_group = AgeGroup(name="KIDS", age_range=AgeRange(5, 12))
    age_repo.insert(age_group)
    pub.fail = True

    r = client.post("/enrollments/", json={"name": "Eve", "age": 10, "cpf": "999.888.777-66"})
    assert r.status_code == 503
    assert r.json()["detail"] == "service unavailable"
