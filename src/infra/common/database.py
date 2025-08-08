from tinydb import TinyDB

from settings import cfg

db = TinyDB(cfg.DB_FILE_PATH)

age_group_table = db.table("age_groups")
enrollment_table = db.table("enrollments")
