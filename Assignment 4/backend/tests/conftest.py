from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_test_env_defaults() -> None:
    os.environ.setdefault("MYSQL_USER", "test_user")
    os.environ.setdefault("MYSQL_PASSWORD", "test_password")
    os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key")


def _ensure_backend_on_path() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    backend_path = str(backend_root)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


_ensure_test_env_defaults()
_ensure_backend_on_path()
