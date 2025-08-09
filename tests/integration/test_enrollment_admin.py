from __future__ import annotations

import time
from collections.abc import Callable

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.services.enrollment_admin import EnrollmentAdminService
from app.usecases.enrollment_admin import EnrollmentAdminUseCase
from domain.enrollment import Enrollment
from infra.api.enrollment_admin import EnrollmentAdminAPI
from infra.dependencies.enrollment_admin import provide_admin_use_case
from infra.enumerators.enrollment import EnrollmentStatus
from infra.repositories.enrollment import EnrollmentRepository


@pytest.fixture
def app_client(tmp_db) -> tuple[TestClient, Callable[[], None], EnrollmentRepository]:
    table = tmp_db.table("enrollments")
    repo = EnrollmentRepository(table=table)
    svc = EnrollmentAdminService(repo)
    uc = EnrollmentAdminUseCase(svc)

    app = FastAPI()
    EnrollmentAdminAPI(app)
    app.dependency_overrides[provide_admin_use_case] = lambda: uc

    client = TestClient(app)

    def _reset():
        table.truncate()

    _reset()
    return client, _reset, repo


def _total(body: dict) -> int:
    return body["meta"]["total_items"]


def _mk_enr(
    *,
    name: str,
    age: int,
    cpf: str,
    status: EnrollmentStatus,
    group: str | None,
    requested_at: int | None = None,
    enrolled_at: int | None = None,
) -> Enrollment:
    ra = requested_at if requested_at is not None else int(time.time()) - 100
    ea = enrolled_at
    if status == EnrollmentStatus.APPROVED:
        ea = ea if ea is not None else int(time.time())
    return Enrollment(
        name=name,
        age=age,
        cpf=cpf,
        status=status,
        requested_at=ra,
        enrolled_at=ea,
        age_group_name=group,
    )


def test_get_by_cpf_200_and_404(app_client):
    client, reset, repo = app_client
    reset()

    e = _mk_enr(
        name="Alice",
        age=21,
        cpf="111.222.333-44",
        status=EnrollmentStatus.APPROVED,
        group="YOUTH",
    )
    repo.insert(e)

    r_ok = client.get("/enrollments/admin/by-cpf/111.222.333-44")
    assert r_ok.status_code == 200
    body = r_ok.json()
    assert body["cpf"] == "111.222.333-44"
    assert body["status"] == "APPROVED"
    assert body["age_group_name"] == "YOUTH"
    assert body["enrolled_at"] is not None
    assert body["requested_at"] is not None

    r_miss = client.get("/enrollments/admin/by-cpf/999.999.999-99")
    assert r_miss.status_code == 404
    assert r_miss.json()["detail"]


def test_list_by_age_group_with_pagination(app_client):
    client, reset, repo = app_client
    reset()

    repo.insert(_mk_enr(name="A1", age=15, cpf="100.000.000-01", status=EnrollmentStatus.APPROVED, group="TEEN"))
    repo.insert(_mk_enr(name="A2", age=16, cpf="100.000.000-02", status=EnrollmentStatus.APPROVED, group="TEEN"))
    repo.insert(_mk_enr(name="B1", age=30, cpf="200.000.000-01", status=EnrollmentStatus.REJECTED, group="ADULT"))

    r1 = client.get("/enrollments/admin/by-group/TEEN?page=1&page_size=1")
    assert r1.status_code == 200
    body1 = r1.json()
    assert _total(body1) == 2
    assert len(body1["items"]) == 1
    assert body1["items"][0]["age_group_name"] == "TEEN"

    r2 = client.get("/enrollments/admin/by-group/TEEN?page=2&page_size=1")
    assert r2.status_code == 200
    body2 = r2.json()
    assert _total(body2) == 2
    assert len(body2["items"]) == 1
    assert body2["items"][0]["age_group_name"] == "TEEN"

    r_empty = client.get("/enrollments/admin/by-group/NONE?page=1&page_size=10")
    assert r_empty.status_code == 200
    assert _total(r_empty.json()) == 0


def test_list_by_name_exact_match_and_pagination(app_client):
    client, reset, repo = app_client
    reset()

    repo.insert(_mk_enr(name="Carol", age=25, cpf="300.000.000-01", status=EnrollmentStatus.APPROVED, group="ADULT"))
    repo.insert(_mk_enr(name="Carol", age=26, cpf="300.000.000-02", status=EnrollmentStatus.REJECTED, group="ADULT"))
    repo.insert(_mk_enr(name="Caroline", age=27, cpf="300.000.000-03", status=EnrollmentStatus.APPROVED, group="ADULT"))

    r_all = client.get("/enrollments/admin/by-name?name=Carol&page=1&page_size=10")
    assert r_all.status_code == 200
    body = r_all.json()
    assert _total(body) == 2
    assert all(item["name"] == "Carol" for item in body["items"])

    r_page = client.get("/enrollments/admin/by-name?name=Carol&page=2&page_size=1")
    assert r_page.status_code == 200
    body2 = r_page.json()
    assert _total(body2) == 2
    assert len(body2["items"]) == 1
    assert body2["items"][0]["name"] == "Carol"

    r_none = client.get("/enrollments/admin/by-name?name=Nobody&page=1&page_size=5")
    assert r_none.status_code == 200
    assert _total(r_none.json()) == 0


def test_list_by_status_filters_and_422_on_invalid_literal(app_client):
    client, reset, repo = app_client
    reset()

    repo.insert(_mk_enr(name="X1", age=20, cpf="400.000.000-01", status=EnrollmentStatus.APPROVED, group="ADULT"))
    repo.insert(_mk_enr(name="X2", age=21, cpf="400.000.000-02", status=EnrollmentStatus.REJECTED, group=None))
    repo.insert(_mk_enr(name="X3", age=22, cpf="400.000.000-03", status=EnrollmentStatus.REJECTED, group=None))

    r_app = client.get("/enrollments/admin/by-status?status=APPROVED&page=1&page_size=10")
    assert r_app.status_code == 200
    body_app = r_app.json()
    assert _total(body_app) == 1
    assert body_app["items"][0]["status"] == "APPROVED"

    r_rej = client.get("/enrollments/admin/by-status?status=REJECTED&page=1&page_size=10")
    assert r_rej.status_code == 200
    body_rej = r_rej.json()
    assert _total(body_rej) == 2
    assert all(item["status"] == "REJECTED" for item in body_rej["items"])

    r_bad = client.get("/enrollments/admin/by-status?status=PENDING")
    assert r_bad.status_code == 422


def test_get_all_with_pagination(app_client):
    client, reset, repo = app_client
    reset()

    repo.insert(_mk_enr(name="N1", age=10, cpf="500.000.000-01", status=EnrollmentStatus.REJECTED, group=None))
    repo.insert(_mk_enr(name="N2", age=11, cpf="500.000.000-02", status=EnrollmentStatus.REJECTED, group=None))
    repo.insert(_mk_enr(name="N3", age=12, cpf="500.000.000-03", status=EnrollmentStatus.APPROVED, group="KIDS"))

    r1 = client.get("/enrollments/admin/all?page=1&page_size=2")
    assert r1.status_code == 200
    body1 = r1.json()
    assert _total(body1) == 3
    assert len(body1["items"]) == 2

    r2 = client.get("/enrollments/admin/all?page=2&page_size=2")
    assert r2.status_code == 200
    body2 = r2.json()
    assert _total(body2) == 3
    assert len(body2["items"]) == 1
