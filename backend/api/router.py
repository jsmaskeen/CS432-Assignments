from fastapi import APIRouter

from api.routes.testing import router as testing_router

api_router = APIRouter()
api_router.include_router(testing_router)
