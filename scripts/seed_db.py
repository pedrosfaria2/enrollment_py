from loguru import logger

from infra.repositories.age_group import AgeGroupRepository
from infra.schemas.age_group import AgeGroup


def run_seed():
    logger.info("Starting Database Seeding")

    try:
        repo = AgeGroupRepository()

        logger.info("Truncating the 'age_groups' table")
        repo.table.truncate()
        logger.success("Table 'age_groups' cleared successfully.")

        groups_to_add = [
            AgeGroup(name="Child", min_age=0, max_age=12),
            AgeGroup(name="Teen", min_age=13, max_age=17),
            AgeGroup(name="Adult", min_age=18, max_age=64),
            AgeGroup(name="Senior", min_age=65, max_age=120),
        ]

        logger.info(f"Adding {len(groups_to_add)} new age groups...")
        for group in groups_to_add:
            repo.insert(group)
            logger.debug(f"Added group: {group.name} ({group.min_age}-{group.max_age})")

        logger.success("All age groups have been added successfully.")

    except Exception as e:
        logger.error(f"An error occurred during database seeding: {e}")

    finally:
        logger.info("Database Seeding Finished")


if __name__ == "__main__":
    run_seed()