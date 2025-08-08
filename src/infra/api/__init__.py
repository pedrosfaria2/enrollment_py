from fastapi import Depends, FastAPI
from fastapi.security import HTTPBasic
from starlette.middleware.cors import CORSMiddleware

from infra.api.age_groups import AgeGroupAPI
from infra.schemas.health import HealthOutput
from settings import Config

security = HTTPBasic()


class APIBuilder:
    def __init__(self, cfg: Config, *, allowed_origins: list[str] | None = None):
        self.cfg = cfg
        show_docs = cfg.ENVIRONMENT in {"dev", "hmg", "test", "development"}
        self.app = FastAPI(
            title="Enrollment API",
            version="1.0.0",
            openapi_url="/openapi.json" if show_docs else None,
            docs_url="/docs" if show_docs else None,
            redoc_url="/redoc" if show_docs else None,
            dependencies=[Depends(security)],
        )
        self._setup_middlewares(allowed_origins or ["*"])

    def __call__(self) -> FastAPI:
        return self.app

    def build_stack(self):
        self._register_health()
        self._register_age_groups()

    def _setup_middlewares(self, origins: list[str]):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _register_health(self):
        @self.app.get("/health", response_model=HealthOutput)
        def health():
            return HealthOutput(environment=self.cfg.ENVIRONMENT)

    def _register_age_groups(self):
        AgeGroupAPI(self.app)
