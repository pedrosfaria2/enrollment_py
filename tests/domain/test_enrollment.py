import time
from dataclasses import FrozenInstanceError

import pytest

from domain.enrollment import Enrollment
from infra.enumerators.enrollment import EnrollmentStatus


def test_enrollment_ok_with_default_status():
    e = Enrollment(name="Alice", age=30, cpf="123.456.789-00")
    assert e.name == "Alice"
    assert e.age == 30
    assert e.cpf == "123.456.789-00"
    assert e.status == EnrollmentStatus.PENDING
    assert e.requested_at is None
    assert e.enrolled_at is None
    assert e.age_group_name is None


def test_enrollment_ok_with_explicit_status():
    e = Enrollment(name="Bob", age=22, cpf="000.000.000-00", status=EnrollmentStatus.REJECTED)
    assert e.status == EnrollmentStatus.REJECTED


def test_negative_age_raises():
    with pytest.raises(ValueError, match="age must be non-negative"):
        Enrollment(name="Carl", age=-1, cpf="123.456.789-00")


@pytest.mark.parametrize(
    "bad_cpf",
    [
        "12345678900",  # no punctuation
        "123.456.789-0",  # too few digits at end
        "123.456.789-000",  # too many digits at end
        "123.456.78-90",  # middle block too short
        "abc.def.ghi-jk",  # letters
        "",  # empty
    ],
)
def test_invalid_cpf_format_raises(bad_cpf):
    with pytest.raises(ValueError, match=r"cpf must match 999\.999\.999-99 format"):
        Enrollment(name="Dana", age=40, cpf=bad_cpf)


def test_dataclass_is_frozen():
    e = Enrollment(name="Eve", age=18, cpf="111.222.333-44")
    with pytest.raises(FrozenInstanceError):
        e.age = 19  # type: ignore[attr-defined]


def test_approved_requires_enrolled_at():
    with pytest.raises(ValueError, match="enrolled_at must be set when status is APPROVED"):
        Enrollment(
            name="Frank",
            age=25,
            cpf="555.666.777-88",
            status=EnrollmentStatus.APPROVED,
            enrolled_at=None,  # invalid for APPROVED
        )

    ok = Enrollment(
        name="Frank",
        age=25,
        cpf="555.666.777-88",
        status=EnrollmentStatus.APPROVED,
        enrolled_at=int(time.time()),
    )
    assert ok.status == EnrollmentStatus.APPROVED
    assert ok.enrolled_at is not None


def test_create_final_new_record_preserves_fields():
    now = int(time.time())
    e = Enrollment.create_final(
        name="Gina",
        age=19,
        cpf="222.333.444-55",
        final_status=EnrollmentStatus.REJECTED,
        existing=None,
        requested_at=now,
        enrolled_at=None,
        age_group_name="Teens",
    )
    assert isinstance(e, Enrollment)
    assert e.name == "Gina"
    assert e.age == 19
    assert e.cpf == "222.333.444-55"
    assert e.status == EnrollmentStatus.REJECTED
    assert e.requested_at == now
    assert e.enrolled_at is None
    assert e.age_group_name == "Teens"


def test_create_final_existing_approved_returns_existing_unchanged():
    existing = Enrollment(
        name="Hank",
        age=30,
        cpf="999.888.777-66",
        status=EnrollmentStatus.APPROVED,
        enrolled_at=int(time.time()),
        requested_at=123,
        age_group_name="Adults",
    )

    out = Enrollment.create_final(
        name="Hank Jr",
        age=22,
        cpf="999.888.777-66",
        final_status=EnrollmentStatus.REJECTED,
        existing=existing,
        requested_at=999999,
        enrolled_at=None,
        age_group_name="Teens",
    )

    assert out is existing or out == existing
    assert out.name == existing.name
    assert out.age == existing.age
    assert out.cpf == existing.cpf
    assert out.status == EnrollmentStatus.APPROVED
    assert out.enrolled_at == existing.enrolled_at
    assert out.requested_at == existing.requested_at
    assert out.age_group_name == existing.age_group_name


def test_create_final_existing_rejected_allows_retry_and_replaces():
    existing = Enrollment(
        name="Ivy",
        age=41,
        cpf="123.123.123-99",
        status=EnrollmentStatus.REJECTED,
        requested_at=111,
        enrolled_at=None,
        age_group_name="Adults",
    )
    now = int(time.time())

    out = Enrollment.create_final(
        name="Ivy",
        age=41,
        cpf="123.123.123-99",
        final_status=EnrollmentStatus.APPROVED,
        existing=existing,
        requested_at=now,
        enrolled_at=now,
        age_group_name="Adults",
    )

    assert out is not existing
    assert out.cpf == existing.cpf
    assert out.status == EnrollmentStatus.APPROVED
    assert out.enrolled_at == now
    assert out.requested_at == now
    assert out.age_group_name == "Adults"


def test_create_final_approved_without_enrolled_at_raises():
    with pytest.raises(ValueError, match="enrolled_at must be set when status is APPROVED"):
        Enrollment.create_final(
            name="Jack",
            age=20,
            cpf="321.654.987-00",
            final_status=EnrollmentStatus.APPROVED,
            existing=None,
            requested_at=int(time.time()),
            enrolled_at=None,  # invalid
            age_group_name="Young",
        )
