from fastapi import APIRouter

from api.routes.admin import router as admin_router
from api.routes.auth import router as auth_router
from api.routes.chat import router as chat_router
from api.routes.locations import router as locations_router
from api.routes.preferences import router as preferences_router
from api.routes.reviews import router as reviews_router
from api.routes.rides import router as rides_router
from api.routes.settlements import router as settlements_router
from api.routes.testing import router as testing_router

api_router = APIRouter()
api_router.include_router(admin_router)
api_router.include_router(auth_router)
api_router.include_router(rides_router)
api_router.include_router(locations_router)
api_router.include_router(preferences_router)
api_router.include_router(reviews_router)
api_router.include_router(settlements_router)
api_router.include_router(chat_router)
api_router.include_router(testing_router)
