from domain.enrollment import Enrollment
from infra.enumerators.enrollment import EnrollmentStatus
from infra.repositories.enrollment import EnrollmentRepository


def test_enrollment_repo_methods(tmp_db):
    repo = EnrollmentRepository(table=tmp_db.table("enrollments"))

    repo.insert(Enrollment(name="Maria", age=20, cpf="123.456.789-09"))

    enr = repo.get_by_id(1)
    assert enr is not None and enr.cpf == "123.456.789-09"

    found = repo.find_by_cpf("123.456.789-09")
    assert found is not None and found.name == "Maria"

    repo.update({"status": EnrollmentStatus.APPROVED}, cpf="123.456.789-09")
    after = repo.find_by_cpf("123.456.789-09")
    assert after is not None
    assert after.status is EnrollmentStatus.APPROVED

    assert repo.exists(cpf="123.456.789-09")
    assert repo.count() == 1

    repo.remove(cpf="123.456.789-09")
    assert repo.count() == 0
