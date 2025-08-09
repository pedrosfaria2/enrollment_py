from collections.abc import Callable

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.services.age_group import AgeGroupService
from app.usecases.age_group import AgeGroupUseCase
from infra.api.age_groups import AgeGroupAPI
from infra.dependencies.age_groups import provide_use_case
from infra.repositories.age_group import AgeGroupRepository
from worker.consumer import EnrollmentRepository


@pytest.fixture
def app_client(tmp_db) -> tuple[TestClient, Callable[[], None]]:
    table = tmp_db.table("age_groups")
    repo = AgeGroupRepository(table=table)
    svc = AgeGroupService(repo, enrollments=EnrollmentRepository())
    uc = AgeGroupUseCase(svc)

    app = FastAPI()
    AgeGroupAPI(app)
    app.dependency_overrides[provide_use_case] = lambda: uc

    client = TestClient(app)

    def _reset():
        table.truncate()

    _reset()
    return client, _reset


def _total(body: dict) -> int:
    return body["meta"]["total_items"]


def test_list_empty(app_client):
    client, reset = app_client
    reset()
    r = client.get("/age-groups/")
    assert r.status_code == 200
    body = r.json()
    assert _total(body) == 0
    assert body["items"] == []


def test_create_ok_and_list(app_client):
    client, reset = app_client
    reset()
    payload = {"name": "ADULT", "min_age": 18, "max_age": 59}
    r = client.post("/age-groups/", json=payload)
    assert r.status_code == 201
    assert r.json() == payload

    r2 = client.get("/age-groups/")
    assert r2.status_code == 200
    body = r2.json()
    assert _total(body) == 1
    assert body["items"][0] == payload


def test_create_duplicate_409_with_message(app_client):
    client, reset = app_client
    reset()
    payload = {"name": "ADULT", "min_age": 18, "max_age": 59}
    assert client.post("/age-groups/", json=payload).status_code == 201
    r = client.post("/age-groups/", json={"name": "ADULT", "min_age": 0, "max_age": 17})
    assert r.status_code == 409
    assert r.json()["detail"]


def test_create_overlap_409_with_message(app_client):
    client, reset = app_client
    reset()
    assert client.post("/age-groups/", json={"name": "ADULT", "min_age": 18, "max_age": 59}).status_code == 201
    r = client.post("/age-groups/", json={"name": "YOUNG", "min_age": 10, "max_age": 20})
    assert r.status_code == 409
    assert r.json()["detail"]


def test_create_422_from_validator(app_client):
    client, reset = app_client
    reset()
    r = client.post("/age-groups/", json={"name": "BAD", "min_age": 10, "max_age": 5})
    assert r.status_code == 422


def test_delete_404_and_delete_204(app_client):
    client, reset = app_client
    reset()
    r = client.delete("/age-groups/NONE")
    assert r.status_code == 404
    assert r.json()["detail"]

    client.post("/age-groups/", json={"name": "ADULT", "min_age": 18, "max_age": 59})
    r2 = client.delete("/age-groups/ADULT")
    assert r2.status_code == 204

    r3 = client.get("/age-groups/")
    assert _total(r3.json()) == 0


def test_pagination_params_and_bounds(app_client):
    client, reset = app_client
    reset()
    for name, lo, hi in [("A", 0, 9), ("B", 10, 19), ("C", 20, 29)]:
        assert client.post("/age-groups/", json={"name": name, "min_age": lo, "max_age": hi}).status_code == 201

    r = client.get("/age-groups/?page=2&page_size=1")
    assert r.status_code == 200
    body = r.json()
    assert _total(body) == 3
    assert len(body["items"]) == 1

    r2 = client.get("/age-groups/?page_size=0")
    assert r2.status_code == 422
