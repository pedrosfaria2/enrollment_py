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
    with pytest.raises(ValueError, match="cpf must match 999\\.999\\.999-99 format"):
        Enrollment(name="Dana", age=40, cpf=bad_cpf)


def test_dataclass_is_frozen():
    e = Enrollment(name="Eve", age=18, cpf="111.222.333-44")
    with pytest.raises(FrozenInstanceError):
        e.age = 19  # type: ignore
