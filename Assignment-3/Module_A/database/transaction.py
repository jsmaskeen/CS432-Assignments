from copy import deepcopy
import json
import os
from threading import Lock
from time import time
from typing import Any, Dict, List, Literal, Optional

class Transaction_operation:
    def __init__(self, action: Literal["insert", "update", "delete"], table_name: str, key: int, row: Optional[Dict[str, Any]] = None):
        self.action = action
        self.table_name = table_name
        self.key = key
        self.row = row

    def to_wal_record(self, tx_id: int, seq: int):
        return {
            "type": "OP",
            "tx_id": tx_id,
            "seq": seq,
            "action": self.action,
            "table_name": self.table_name,
            "key": self.key,
            "row": self.row,
            "ts": time(),
        }

    def from_wal_record(cls, record: Dict[str, Any]):
        return cls(
            action=record["action"],
            table_name=record["table_name"],
            key=record["key"],
            row=record.get("row"),
        )


class Transaction:
    _wal_write_lock = Lock()

    def __init__(self, db, wal_path: Optional[str] = None):
        self.db = db
        self.tx_id = self.db.next_transaction_id()
        self.operations: List[Transaction_operation] = []
        self.staged_rows: Dict[str, Dict[int, Optional[Dict[str, Any]]]] = {}
        self._op_seq = 0
        self._has_logged_begin = False
        self.wal_path = wal_path if wal_path is not None else self._default_wal_path()

    def _default_wal_path(self):
        wal_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "wal"))
        db_name = getattr(self.db, "db_name", "default")
        return os.path.join(wal_dir, f"{db_name}.wal.jsonl")

    def _append_wal_record(self, record: Dict[str, Any], fsync: bool = False):
        self.append_wal_record(self.wal_path, record, fsync=fsync)

    @classmethod
    def append_wal_record(cls, wal_path: str, record: Dict[str, Any], fsync: bool = False):
        os.makedirs(os.path.dirname(wal_path), exist_ok=True)
        line = json.dumps(record, separators=(",", ":"), sort_keys=True)

        with cls._wal_write_lock:
            with open(wal_path, "a", encoding="utf-8") as wal_file:
                wal_file.write(line + "\n")
                if fsync:
                    wal_file.flush()
                    os.fsync(wal_file.fileno())

    def _log_begin_if_needed(self):
        if self._has_logged_begin:
            return

        self._append_wal_record(
            {
                "type": "BEGIN",
                "tx_id": self.tx_id,
                "ts": time(),
            }
        )
        self._has_logged_begin = True

    def _log_operation(self, operation: Transaction_operation):
        self._append_wal_record(operation.to_wal_record(self.tx_id, self._op_seq))
        self._op_seq += 1

    def log_commit(self):
        self._log_begin_if_needed()
        self._append_wal_record(
            {
                "type": "COMMIT",
                "tx_id": self.tx_id,
                "ts": time(),
            },
            fsync=True,
        )

    def log_rollback(self):
        self._log_begin_if_needed()
        self._append_wal_record(
            {
                "type": "ROLLBACK",
                "tx_id": self.tx_id,
                "ts": time(),
            },
            fsync=True,
        )

    @classmethod
    def read_wal_records(cls, wal_path: str):
        if not os.path.exists(wal_path):
            return []

        records: List[Dict[str, Any]] = []
        with open(wal_path, "r", encoding="utf-8") as wal_file:
            for line in wal_file:
                text = line.strip()
                if not text:
                    continue
                try:
                    records.append(json.loads(text))
                except json.JSONDecodeError:
                    # Treat malformed JSON as an incomplete tail due to crash and stop replay.
                    break

        return records

    @classmethod
    def committed_operations_from_wal(cls, wal_path: str):
        records = cls.read_wal_records(wal_path)
        tx_ops: Dict[int, List[Transaction_operation]] = {}
        committed_tx_ids: List[int] = []
        rolled_back_tx_ids = set()

        for record in records:
            rec_type = record.get("type")
            tx_id = record.get("tx_id")

            if rec_type == "OP":
                tx_ops.setdefault(tx_id, []).append(Transaction_operation.from_wal_record(record))
            elif rec_type == "COMMIT":
                committed_tx_ids.append(tx_id)
            elif rec_type == "ROLLBACK":
                rolled_back_tx_ids.add(tx_id)

        ordered_ops: List[Transaction_operation] = []
        seen_tx_ids = set()
        for tx_id in committed_tx_ids:
            if tx_id in rolled_back_tx_ids:
                continue
            if tx_id in seen_tx_ids:
                continue
            ordered_ops.extend(tx_ops.get(tx_id, []))
            seen_tx_ids.add(tx_id)

        return ordered_ops

    @classmethod
    def clear_wal(cls, wal_path: str):
        os.makedirs(os.path.dirname(wal_path), exist_ok=True)
        with open(wal_path, "w", encoding="utf-8"):
            pass

    def staged_lookup(self, table_name: str, key: int):
        table_rows = self.staged_rows.get(table_name)
        if table_rows is None or key not in table_rows:
            return False, None

        row = table_rows[key]
        if row is None:
            return True, None

        return True, deepcopy(row)

    def staged_rows_for_table(self, table_name: str):
        table_rows = self.staged_rows.get(table_name, {})
        result: Dict[int, Optional[Dict[str, Any]]] = {}

        for key, row in table_rows.items():
            result[key] = None if row is None else deepcopy(row)

        return result

    def stage_insert(self, table_name: str, key: int, row: Dict[str, Any]):
        self._log_begin_if_needed()
        cur_row = deepcopy(row)
        operation = Transaction_operation("insert", table_name, key, cur_row)
        self.operations.append(operation)
        self.staged_rows.setdefault(table_name, {})[key] = cur_row
        self._log_operation(operation)

    def stage_update(self, table_name: str, key: int, row: Dict[str, Any]):
        self._log_begin_if_needed()
        cur_row = deepcopy(row)
        operation = Transaction_operation("update", table_name, key, cur_row)
        self.operations.append(operation)
        self.staged_rows.setdefault(table_name, {})[key] = cur_row
        self._log_operation(operation)

    def stage_delete(self, table_name: str, key: int):
        self._log_begin_if_needed()
        table_rows = self.staged_rows.setdefault(table_name, {})
        if key in table_rows and table_rows[key] is None:
            return

        operation = Transaction_operation("delete", table_name, key, None)
        self.operations.append(operation)
        table_rows[key] = None
        self._log_operation(operation)

    def commit(self):
        self.db.commit_transaction(self)

    def rollback(self):
        self.db.rollback_transaction(self)
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        return False