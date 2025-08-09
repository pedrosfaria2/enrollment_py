from domain.age_group import AgeGroup, AgeRange
from infra.repositories.age_group import AgeGroupRepository


def test_pagination_and_search(tmp_db):
    repo = AgeGroupRepository(table=tmp_db.table("age_groups"))

    for i in range(10):
        repo.insert(AgeGroup(name=f"G{i}", age_range=AgeRange(i, i)))

    page1 = repo.get_all(limit=3)
    page2 = repo.get_all(offset=3, limit=3)
    page3 = repo.get_all(offset=6, limit=3)
    assert [len(page1), len(page2), len(page3)] == [3, 3, 3]

    matches = repo.search_by_fields(name="G1")
    assert len(matches) == 1 and matches[0].name == "G1"
