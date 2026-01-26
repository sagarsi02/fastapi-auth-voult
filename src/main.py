"""Application entrypoint and FastAPI app factory."""

from fastapi import FastAPI
from src.api.routes.users import user_router
from src.api.routes.welcome import welcome_router
from src.logging import get_logger, setup_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    setup_logging()
    logger = get_logger(__name__)
    app = FastAPI()

    # Register API routers for modular endpoint grouping.
    app.include_router(welcome_router)
    app.include_router(user_router, prefix="/users", tags=["users"])

    logger.info("FastAPI application initialized")
    return app


# ASGI app instance used by uvicorn.
app = create_app()
