from dataclasses import FrozenInstanceError

import pytest

from domain.age_group import (
    AgeGroup,
    AgeGroupOverlapError,
    AgeRange,
    DuplicateAgeGroupError,
)


def ag(name: str, lo: int, hi: int) -> AgeGroup:
    return AgeGroup(name=name, age_range=AgeRange(lo, hi))


def test_age_range_allows_min_eq_max():
    r = AgeRange(10, 10)
    assert r.min_age == 10 and r.max_age == 10


def test_age_range_raises_when_min_gt_max():
    with pytest.raises(ValueError, match="min_age must be ≤ max_age"):
        AgeRange(11, 10)


@pytest.mark.parametrize(
    "a1,a2,b1,b2,expected",
    [
        (10, 20, 20, 30, True),  # touching at boundary
        (10, 20, 21, 30, False),  # disjoint
        (0, 0, 0, 0, True),  # identical points
        (0, 5, 6, 10, False),  # gap of 1
        (5, 10, 0, 5, True),  # touching at left boundary
    ],
)
def test_age_range_overlaps(a1, a2, b1, b2, expected):
    assert AgeRange(a1, a2).overlaps(AgeRange(b1, b2)) is expected


def test_create_raises_duplicate_name_if_in_existing_list():
    existing = [ag("ADULT", 18, 59)]
    with pytest.raises(DuplicateAgeGroupError):
        AgeGroup.create("ADULT", 0, 17, existing)


def test_create_raises_overlap_if_range_overlaps_any_existing():
    existing = [ag("ADULT", 18, 59)]
    with pytest.raises(AgeGroupOverlapError):
        AgeGroup.create("YOUNG", 10, 20, existing)  # 18–20 overlaps


def test_create_ok_when_unique_name_and_non_overlapping():
    existing = [ag("ADULT", 18, 59)]
    res = AgeGroup.create("SENIOR", 60, 120, existing)
    assert res.name == "SENIOR"
    assert res.age_range.min_age == 60
    assert res.age_range.max_age == 120


def test_age_range_is_frozen():
    r = AgeRange(0, 10)
    with pytest.raises(FrozenInstanceError):
        r.min_age = 1  # type: ignore
