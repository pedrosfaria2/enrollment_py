from fastapi import Depends, FastAPI
from starlette.middleware.cors import CORSMiddleware

from infra.api.age_groups import AgeGroupAPI
from infra.api.enrollment import EnrollmentAPI
from infra.api.enrollment_admin import EnrollmentAdminAPI
from infra.common.logging import LogAPIRoute
from infra.schemas.health import HealthOutput
from infra.security.basic_auth import BasicAuthGuard
from settings import Config


class APIBuilder:
    """Builder for FastAPI application with enrollment endpoints.
    
    Configures FastAPI app with CORS, authentication, and API routes.
    """
    
    def __init__(self, cfg: Config, *, allowed_origins: list[str] | None = None) -> None:
        """Initialize API builder with configuration.
        
        Args:
            cfg: Application configuration
            allowed_origins: CORS allowed origins (default: ["*"])
        """
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
        """Return the FastAPI application instance.
        
        Returns:
            Configured FastAPI application
        """
        return self.app

    def build_stack(self) -> None:
        """Register all API routes and endpoints."""
        self._register_health()  # public
        self._register_age_groups()  # protected
        self._register_enrollment()  # public
        self._register_enrollment_admin()  # protected

    def _setup_middlewares(self, origins: list[str]) -> None:
        """Setup CORS middleware for the application.
        
        Args:
            origins: List of allowed origins for CORS
        """
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _register_health(self) -> None:
        """Register health check endpoint."""
        @self.app.get("/health", response_model=HealthOutput)
        def health() -> HealthOutput:
            """Health check endpoint.
            
            Returns:
                Health status with environment information
            """
            return HealthOutput(environment=self.cfg.ENVIRONMENT)

    def _register_age_groups(self) -> None:
        """Register age groups API with authentication."""
        AgeGroupAPI(self.app, dependencies=[Depends(self._auth)])

    def _register_enrollment(self) -> None:
        """Register enrollment API without authentication."""
        EnrollmentAPI(self.app)

    def _register_enrollment_admin(self) -> None:
        """Register enrollment admin API with authentication."""
        EnrollmentAdminAPI(self.app, dependencies=[Depends(self._auth)])
