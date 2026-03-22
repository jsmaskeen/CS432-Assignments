from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class RequestContext:
    request_id: str | None = None
    actor_member_id: int | None = None
    actor_username: str | None = None
    actor_role: str | None = None


_request_context: ContextVar[RequestContext] = ContextVar("request_context", default=RequestContext())


def set_request_context(*, request_id: str, actor_member_id: int | None, actor_username: str | None, actor_role: str | None) -> None:
    _request_context.set(
        RequestContext(
            request_id=request_id,
            actor_member_id=actor_member_id,
            actor_username=actor_username,
            actor_role=actor_role,
        )
    )


def get_request_context() -> RequestContext:
    return _request_context.get()


def clear_request_context() -> None:
    _request_context.set(RequestContext())
