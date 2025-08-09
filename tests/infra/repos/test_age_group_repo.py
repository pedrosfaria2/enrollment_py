from domain.age_group import AgeGroup, AgeRange
from infra.repositories.age_group import AgeGroupRepository


def test_age_group_repo(tmp_db):
    repo = AgeGroupRepository(table=tmp_db.table("age_groups"))

    repo.insert(AgeGroup(name="Child", age_range=AgeRange(0, 12)))
    repo.insert(AgeGroup(name="Adult", age_range=AgeRange(18, 64)))
    repo.insert(AgeGroup(name="Senior", age_range=AgeRange(65, 120)))

    adult = repo.get_by_id(2)
    assert adult is not None
    assert adult.name == "Adult"

    child = repo.find_by_name("Child")
    assert child is not None

    repo.update({"max_age": 13}, name="Child")
    updated = repo.find_by_name("Child")
    assert updated is not None and updated.age_range.max_age == 13

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
