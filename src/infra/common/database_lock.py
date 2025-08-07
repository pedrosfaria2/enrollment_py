from filelock import FileLock

from settings import cfg

db_lock = FileLock(cfg.DB_FILE_PATH + ".lock", timeout=cfg.DB_LOCK_TIMEOUT)
