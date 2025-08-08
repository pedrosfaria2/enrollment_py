from infra.repositories.age_group import AgeGroupRepository
from infra.schemas.age_group import AgeGroup


def test_age_group_repo(tmp_db):
    repo = AgeGroupRepository(table=tmp_db.table("age_groups"))

    repo.insert(AgeGroup(name="Child", min_age=0, max_age=12))
    repo.insert(AgeGroup(name="Adult", min_age=18, max_age=64))
    repo.insert(AgeGroup(name="Senior", min_age=65, max_age=120))

    adult = repo.get_by_id(2)
    assert adult is not None
    assert adult.name == "Adult"

    child = repo.find_by_name("Child")
    assert child is not None

    repo.update({"max_age": 13}, name="Child")
    updated = repo.find_by_name("Child")
    assert updated is not None and updated.max_age == 13

    assert repo.exists(name="Senior")
    assert repo.count() == 3

    page1 = repo.get_all(limit=2)
    page2 = repo.get_all(offset=2, limit=2)
    assert len(page1) == 2 and len(page2) == 1

    repo.remove(name="Adult")
    assert repo.count() == 2

    repo.remove(name="Child")
    repo.remove(name="Senior")
    assert repo.count() == 0
