from fastapi import Depends, FastAPI
from starlette.middleware.cors import CORSMiddleware

from infra.api.age_groups import AgeGroupAPI
from infra.api.enrollment import EnrollmentAPI
from infra.common.logging import LogAPIRoute
from infra.schemas.health import HealthOutput
from infra.security.basic_auth import BasicAuthGuard
from settings import Config


class APIBuilder:
    def __init__(self, cfg: Config, *, allowed_origins: list[str] | None = None) -> None:
        self.cfg = cfg
        show_docs = cfg.ENVIRONMENT in {"dev", "hmg", "test", "development"}

        self.app = FastAPI(
            title="Enrollment API",
            version="1.0.0",
            openapi_url="/openapi.json" if show_docs else None,
            docs_url="/docs" if show_docs else None,
            redoc_url="/redoc" if show_docs else None,
        )

        self.app.router.route_class = LogAPIRoute
        self._auth = BasicAuthGuard(cfg.API_USERNAME, cfg.API_PASSWORD)
        self._setup_middlewares(allowed_origins or ["*"])

    def __call__(self) -> FastAPI:
        return self.app

    def build_stack(self) -> None:
        self._register_health()  # public
        self._register_age_groups()  # protected
        self._register_enrollment()  # public

    def _setup_middlewares(self, origins: list[str]) -> None:
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _register_health(self) -> None:
        @self.app.get("/health", response_model=HealthOutput)
        def health() -> HealthOutput:
            return HealthOutput(environment=self.cfg.ENVIRONMENT)

    def _register_age_groups(self) -> None:
        AgeGroupAPI(self.app, dependencies=[Depends(self._auth)])

    def _register_enrollment(self) -> None:
        EnrollmentAPI(self.app)
