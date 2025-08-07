from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from infra.schemas.health import HealthOutput
from settings import Config


class APIBuilder:
    def __init__(self, settings: Config):
        self.cfg = settings
        self.app = FastAPI(
            title="Enrollment API",
            description="API for enrollment management",
            version="1.0.0",
            openapi_url=("/openapi.json" if self.cfg.ENVIRONMENT in ("dev", "hmg", "test", "development") else None),
            docs_url=("/docs" if self.cfg.ENVIRONMENT in ("dev", "hmg", "test", "development") else None),
            redoc_url=("/redoc" if self.cfg.ENVIRONMENT in ("dev", "hmg", "test", "development") else None),
        )

    def build_stack(self):
        self._middlewares()
        self._health_api()

    def _middlewares(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _health_api(self):
        @self.app.get("/", response_model=HealthOutput, status_code=200)
        def health_status():
            return HealthOutput(environment=self.cfg.ENVIRONMENT).model_dump()
