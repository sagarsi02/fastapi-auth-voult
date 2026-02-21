"""Welcome/landing route definitions."""

from fastapi import APIRouter


welcome_router = APIRouter()


@welcome_router.get("/")
def landing_page():
    """
    Return a simple welcome message for the root URL.
    """
    return {"Greet": "Welcome to Our Landing Page - Auth Voult"}
