from __future__ import annotations

from threading import Lock

_lock = Lock()
_failures_by_hook: dict[str, int] = {}


def enable_failures(hook: str, fail_count: int = 1) -> int:
    normalized = hook.strip().lower()
    if not normalized:
        raise ValueError("hook is required")
    if fail_count < 1:
        raise ValueError("fail_count must be >= 1")

    with _lock:
        _failures_by_hook[normalized] = _failures_by_hook.get(normalized, 0) + fail_count
        return _failures_by_hook[normalized]


def consume_failure(hook: str) -> bool:
    normalized = hook.strip().lower()
    if not normalized:
        return False

    with _lock:
        remaining = _failures_by_hook.get(normalized, 0)
        if remaining <= 0:
            return False
        remaining -= 1
        if remaining == 0:
            _failures_by_hook.pop(normalized, None)
        else:
            _failures_by_hook[normalized] = remaining
        return True


def reset_failures() -> None:
    with _lock:
        _failures_by_hook.clear()


def snapshot_failures() -> dict[str, int]:
    with _lock:
        return dict(sorted(_failures_by_hook.items()))
