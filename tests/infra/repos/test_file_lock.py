from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tinydb import JSONStorage, TinyDB

from domain.age_group import AgeGroup, AgeRange
from infra.repositories.age_group import AgeGroupRepository


def _worker(path: str, batch):
    db = TinyDB(path, storage=JSONStorage)
    try:
        repo = AgeGroupRepository(table=db.table("age_groups"))
        for rec in batch:
            repo.insert(rec)
    finally:
        db.close()


def test_file_lock(tmp_path):
    db_path = Path(tmp_path) / "lock.json"
    batches = [[AgeGroup(name=f"g{t}_{i}", age_range=AgeRange(i, i)) for i in range(10)] for t in range(5)]

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = []
        for batch in batches:
            future = pool.submit(_worker, str(db_path), batch)
            futures.append(future)

        for future in futures:
            future.result()

    repo = AgeGroupRepository(table=TinyDB(db_path, storage=JSONStorage).table("age_groups"))
    assert repo.count() == 50
