import logging
import time
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from starlette.responses import Response

from api.router import api_router
from core.audit import setup_audit_logger
from core.config import settings
from core.logging_config import setup_logging
from core.request_context import clear_request_context, set_request_context
from core.security import decode_access_token_payload
from db.session import init_auth_tables

setup_logging(settings.LOG_LEVEL)
setup_audit_logger()
logger = logging.getLogger("rajak.app")

app = FastAPI(title=settings.APP_NAME)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
	start = time.perf_counter()
	request_id = str(uuid4())
	actor_member_id: int | None = None
	actor_username: str | None = None
	actor_role: str | None = None
	auth_header = request.headers.get("authorization", "")
	if auth_header.lower().startswith("bearer "):
		token = auth_header.split(" ", 1)[1].strip()
		payload = decode_access_token_payload(token)
		subject = payload.get("sub") if payload else None
		if subject is not None and subject.isdigit():
			actor_member_id = int(subject)
			claim_username = payload.get("usr") if payload else None
			claim_role = payload.get("role") if payload else None
			if isinstance(claim_username, str):
				actor_username = claim_username
			if isinstance(claim_role, str):
				actor_role = claim_role

	set_request_context(
		request_id=request_id,
		actor_member_id=actor_member_id,
		actor_username=actor_username,
		actor_role=actor_role,
	)
	request.state.request_id = request_id

	logger.info("request.start method=%s path=%s request_id=%s", request.method, request.url.path, request_id)
	try:
		response = await call_next(request)
	except Exception:
		logger.exception("request.error method=%s path=%s request_id=%s", request.method, request.url.path, request_id)
		raise
	finally:
		clear_request_context()

	elapsed_ms = (time.perf_counter() - start) * 1000
	logger.info(
		"request.end method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
		request.method,
		request.url.path,
		response.status_code,
		elapsed_ms,
		request_id,
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
