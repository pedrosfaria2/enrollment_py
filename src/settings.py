import os
from pathlib import Path
from sys import stderr

from dotenv import load_dotenv
from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent


class Config(BaseSettings):
    ENVIRONMENT: str = Field(
        default=os.getenv("ENVIRONMENT", "dev"),
        description="Project execution environment",
    )
    DB_FILE_PATH: str = Field(
        default=os.getenv("DB_FILE_PATH", str(PROJECT_ROOT / "suthub_db.json")),
        description="File path for the application's TinyDB database",
    )
    DB_LOCK_TIMEOUT: int = Field(ge=1, default=10, description="Database lock timeout in seconds")
    RABBITMQ_HOST: str = Field(
        default=os.getenv("RABBITMQ_HOST", "localhost"),
        description="RabbitMQ host",
    )
    RABBITMQ_PORT: int = Field(
        default=int(os.getenv("RABBITMQ_PORT", "5672")),
        description="RabbitMQ port",
    )
    RABBITMQ_USER: str = Field(
        default=os.getenv("RABBITMQ_USER", "guest"),
        description="RabbitMQ user",
    )
    RABBITMQ_PASS: str = Field(
        default=os.getenv("RABBITMQ_PASS", "guest"),
        description="RabbitMQ password",
    )
    RABBITMQ_VHOST: str = Field(
        default=os.getenv("RABBITMQ_VHOST", "/"),
        description="RabbitMQ virtual host",
    )

    @property
    def RABBITMQ_URL(self) -> str:  # noqa
        """RabbitMQ connection URL"""
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"

    def configure_logging(self):
        logger.remove()
        logger.add(
            stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO" if self.ENVIRONMENT == "prod" else "DEBUG",
        )


cfg = Config()
cfg.configure_logging()
