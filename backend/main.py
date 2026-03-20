import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from starlette.responses import Response

from api.router import api_router
from core.config import settings
from core.logging_config import setup_logging
from db.session import init_auth_tables

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("rajak.app")

app = FastAPI(title=settings.APP_NAME)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
	start = time.perf_counter()
	logger.info("request.start method=%s path=%s", request.method, request.url.path)
	try:
		response = await call_next(request)
	except Exception:
		logger.exception("request.error method=%s path=%s", request.method, request.url.path)
		raise

	elapsed_ms = (time.perf_counter() - start) * 1000
	logger.info(
		"request.end method=%s path=%s status=%s duration_ms=%.2f",
		request.method,
		request.url.path,
		response.status_code,
		elapsed_ms,
	)
	return response


app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		settings.FRONTEND_ORIGIN,
		"http://localhost:5173",
		"http://127.0.0.1:5173",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
	logger.info("startup.begin")
	init_auth_tables()
	logger.info("startup.ready")
