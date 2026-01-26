from fastapi import APIRouter


welcome_router = APIRouter()

@welcome_router.get("/")
def landing_page():
    """
        Welcome or Landing Url
    """
    return {"Greet": "Welcome to Our Landing Page"}
