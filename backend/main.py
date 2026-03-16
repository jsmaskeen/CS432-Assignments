from fastapi import FastAPI

from api.router import api_router
from core.config import settings

app = FastAPI(title=settings.APP_NAME)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
