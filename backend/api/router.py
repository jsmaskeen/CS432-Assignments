from fastapi import APIRouter

from api.routes.auth import router as auth_router
from api.routes.rides import router as rides_router
from api.routes.testing import router as testing_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(rides_router)
api_router.include_router(testing_router)
