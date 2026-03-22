import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import settings
from core.request_context import get_request_context


def setup_audit_logger() -> None:
    logger = logging.getLogger("rajak.audit")
    if logger.handlers:
        return

    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_path = Path(settings.AUDIT_LOG_FILE)
    if not log_path.is_absolute():
        log_path = Path(__file__).resolve().parents[1] / log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


def audit_event(
    *,
    action: str,
    status: str,
    actor_member_id: int | None,
    actor_username: str | None,
    details: dict[str, Any] | None = None,
) -> None:
    ctx = get_request_context()
    effective_actor_member_id = actor_member_id if actor_member_id is not None else ctx.actor_member_id
    effective_actor_username = actor_username if actor_username is not None else ctx.actor_username
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "request_id": ctx.request_id,
        "action": action,
        "status": status,
        "actor_member_id": effective_actor_member_id,
        "actor_username": effective_actor_username,
        "details": details or {},
    }
    logging.getLogger("rajak.audit").info(json.dumps(payload, ensure_ascii=True))
