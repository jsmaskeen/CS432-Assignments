from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


from db.session import engine


def _strip_non_executable_comments(sql_text: str) -> str:
    # Drop line comments.
    no_line_comments = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or stripped.startswith("#"):
            continue
        no_line_comments.append(line)

    text = "\n".join(no_line_comments)

    # Drop block comments except versioned MySQL executable comments: /*! ... */
    text = re.sub(r"/\*(?!\!)(.|\n)*?\*/", "", text)
    return text


def _split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []

    in_single = False
    in_double = False
    in_backtick = False
    escaped = False

    for ch in sql_text:
        buffer.append(ch)

        if escaped:
            escaped = False
            continue

        if ch == "\\":
            escaped = True
            continue

        if ch == "'" and not in_double and not in_backtick:
            in_single = not in_single
            continue

        if ch == '"' and not in_single and not in_backtick:
            in_double = not in_double
            continue

        if ch == "`" and not in_single and not in_double:
            in_backtick = not in_backtick
            continue

        if ch == ";" and not in_single and not in_double and not in_backtick:
            stmt = "".join(buffer).strip()
            buffer = []
            if stmt:
                statements.append(stmt)

    trailing = "".join(buffer).strip()
    if trailing:
        statements.append(trailing)

    return statements


def _execute_dump(dump_path: Path) -> int:
    raw_sql = dump_path.read_text(encoding="utf-8", errors="ignore")
    cleaned_sql = _strip_non_executable_comments(raw_sql)
    cleaned_sql = cleaned_sql.replace('%', '%%')
    statements = _split_sql_statements(cleaned_sql)

    executed = 0
    with engine.begin() as conn:
        for stmt in statements:
            if not stmt:
                continue
            conn.exec_driver_sql(stmt)
            executed += 1

    return executed


def _post_reset_auth() -> None:
    with engine.begin() as conn:
        conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS=0")
        conn.exec_driver_sql("TRUNCATE TABLE Auth_Credentials")
        conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS=1")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reset DB from SQL dump without mysql CLI (uses SQLAlchemy/PyMySQL)."
    )
    parser.add_argument(
        "--dump",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "SQL-Dump" / "dump.sql",
        help="Path to SQL dump file.",
    )
    parser.add_argument(
        "--skip-auth-truncate",
        action="store_true",
        help="Skip truncating Auth_Credentials after dump load.",
    )
    args = parser.parse_args()

    dump_path = args.dump.resolve()
    if not dump_path.exists():
        print(f"Error: dump file not found at {dump_path}")
        return 1

    print(f"Loading SQL dump from: {dump_path}")
    try:
        executed = _execute_dump(dump_path)
        print(f"Executed {executed} SQL statements from dump.")

        if not args.skip_auth_truncate:
            _post_reset_auth()
            print("Auth_Credentials truncated.")

        print("Database cleanup/reset complete.")
        return 0
    except Exception as exc:
        print(f"Database cleanup failed: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
