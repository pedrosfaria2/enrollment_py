"""Main application entry point for enrollment management API.

This module sets up and configures the FastAPI application with all routes,
middleware, and dependencies through the APIBuilder.
"""
import uvicorn

from infra.api import APIBuilder
from settings import cfg

# Initialize API builder with configuration
builder = APIBuilder(cfg)
builder.build_stack()

# Create FastAPI application instance
app = builder()


def main() -> None:
    """Start the FastAPI server with uvicorn.
    
    Runs the enrollment API server on host 0.0.0.0:8003 with
    hot reload enabled for development.
    """
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True, access_log=True)


if __name__ == "__main__":
    main()
