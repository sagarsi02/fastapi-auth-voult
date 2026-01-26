from fastapi import FastAPI
from src.api.routes.users import user_router
from src.api.routes.welcome import welcome_router


def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(welcome_router)
    app.include_router(user_router, prefix="/users", tags=["users"])

    return app


app = create_app()
