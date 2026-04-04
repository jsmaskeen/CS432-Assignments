
import sys
import os
import importlib.util
from copy import deepcopy
from time import time

ASSN2_MODULE_A = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Assignment-2/Module_A"))

assn2_db_mgr_path = os.path.join(ASSN2_MODULE_A, "database", "db_manager.py")
spec = importlib.util.spec_from_file_location("assn2_database.db_manager", assn2_db_mgr_path)
assn2_db_manager = importlib.util.module_from_spec(spec)
sys.modules["assn2_database.db_manager"] = assn2_db_manager
spec.loader.exec_module(assn2_db_manager)

BaseDatabase = assn2_db_manager.Database
BaseDatabaseManager = assn2_db_manager.DatabaseManager

from .transaction import Transaction, Transaction_operation
from .table import Table
from typing import List, Dict, Any, Literal, Optional, Union

class Database(BaseDatabase):
    def __init__(self, db_name: str = "default"):
        super().__init__()
        self.db_name = db_name
        self.active_transaction: Union[Transaction, None] = None
        self._replaying_wal = False
        wal_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "wal"))
        self.wal_path = os.path.join(wal_dir, f"{self.db_name}.wal.jsonl")

    def set_wal_path(self, wal_path: str):
        self.wal_path = wal_path

    def next_transaction_id(self):
        next_id = 1
        records = Transaction.read_wal_records(self.wal_path)
        for record in records:
            tx_id = record.get("tx_id")
            if isinstance(tx_id, int) and tx_id >= next_id:
                next_id = tx_id + 1
        return next_id
    
    def create_table(
        self,
        name: str,
        columns: List[str],
        primary_key: str,
        indexer: Literal["brute", "bplus"] = "bplus",
        degree: int = 4,
        foreign_keys: Optional[List[Dict[str, Any]]] = None,
        integrity_checks: Optional[List[Dict[str, Any]]] = None,
    ):
        if name in self.tables:
            raise ValueError(f"Table '{name}' already exists")
        
        self.tables[name] = Table(
            name=name,
            columns=columns,
            primary_key=primary_key,
            indexer=indexer,
            degree=degree,
            foreign_keys=foreign_keys,
            integrity_checks=integrity_checks,
            db_manager=self 
        )

        if not self._replaying_wal:
            Transaction.append_wal_record(
                self.wal_path,
                {
                    "type": "DDL",
                    "action": "CREATE_TABLE",
                    "name": name,
                    "columns": columns,
                    "primary_key": primary_key,
                    "indexer": indexer,
                    "degree": degree,
                    "foreign_keys": foreign_keys,
                    "ts": time(),
                },
                fsync=True,
            )

        return self.tables[name]

    def drop_table(self, name: str):
        if name not in self.tables:
            raise ValueError(f"Table '{name}' does not exist")

        super().drop_table(name)
        if not self._replaying_wal:
            Transaction.append_wal_record(
                self.wal_path,
                {
                    "type": "DDL",
                    "action": "DROP_TABLE",
                    "name": name,
                    "ts": time(),
                },
                fsync=True,
            )
    
    def begin_transaction(self):
        if self.active_transaction is not None:
            raise ValueError(f"Cannot begin a new transaction while transaction {self.active_transaction} is active")
        self.active_transaction = Transaction(self, wal_path=self.wal_path)
        return self.active_transaction

    def run_autocommit(self, operation):
        tx = self.begin_transaction()
        try:
            result = operation(tx)
            self.commit_transaction(tx)
            return result
        except Exception:
            if self.active_transaction is tx:
                try:
                    self.rollback_transaction(tx)
                except Exception:
                    self.active_transaction = None
            raise

    def validate_transaction(self, tx: Transaction):
        if tx is None:
            raise ValueError("Transaction is required")
        if tx.db is not self:
            raise ValueError("Transaction belongs to a different database")
        if self.active_transaction is not tx:
            raise ValueError("Transaction is not active on this database")

    def _acquire_transaction_table_locks(self, tx: Transaction):
        locked_tables = []
        touched_table_names = sorted({op.table_name for op in tx.operations})

        for table_name in touched_table_names:
            table = self.get_table(table_name)
            table.acquire_table_lock()
            locked_tables.append(table)

        return locked_tables

    def _release_transaction_table_locks(self, locked_tables):
        for table in reversed(locked_tables):
            table.release_table_lock()

    def apply_operation(self, op: Transaction_operation, undo_log: Optional[List[Transaction_operation]] = None):
        table = self.get_table(op.table_name)
        
        if op.action == "insert":
            if op.row is None:
                raise ValueError("Corrupt transaction operation: missing row for insert")
            if table.select(op.key) is not None:
                raise ValueError(f"Duplicate primary key: {op.key}")
            table._apply_insert_direct(op.row)
            if undo_log is not None:
                undo_log.append(Transaction_operation("delete", op.table_name, op.key))
            return

        if op.action == "update":
            if op.row is None:
                raise ValueError("Corrupt transaction operation: missing row for update")
            previous = table.select(op.key)
            if previous is None:
                raise ValueError(f"Cannot update missing key {op.key} in table {op.table_name}")
            table._apply_update_direct(op.key, op.row)
            if undo_log is not None:
                undo_log.append(Transaction_operation("update", op.table_name, op.key, deepcopy(previous)))
            return

        if op.action == "delete":
            previous = table.select(op.key)
            if previous is None:
                raise ValueError(f"Cannot delete missing key {op.key} from table {op.table_name}")
            table._apply_delete_direct(op.key)
            if undo_log is not None:
                undo_log.append(Transaction_operation("insert", op.table_name, op.key, deepcopy(previous)))
            return

        raise ValueError(f"Unsupported transaction action: {op.action}")

    def apply_undo_operation(self, op: Transaction_operation):
        table = self.get_table(op.table_name)
        if op.action == "insert":
            if op.row is None:
                raise ValueError("Corrupt undo operation: missing row for insert")
            table._apply_insert_direct(op.row)
            return
        if op.action == "update":
            if op.row is None:
                raise ValueError("Corrupt undo operation: missing row for update")
            table._apply_update_direct(op.key, op.row)
            return
        if op.action == "delete":
            table._apply_delete_direct(op.key)
            return
        raise ValueError(f"Unsupported undo action: {op.action}")
        
    def commit_transaction(self, tx: Transaction):
        self.validate_transaction(tx)
        if len(tx.operations) == 0:
            self.active_transaction = None
            return

        undo_log: List[Transaction_operation] = []
        locked_tables = self._acquire_transaction_table_locks(tx)

        try:
            for op in tx.operations:
                self.apply_operation(op, undo_log)

            # Commit is considered durable only after COMMIT reaches WAL and is fsync-ed.
            tx.log_commit()

        except Exception as exc:
            for undo_op in reversed(undo_log):
                try:
                    self.apply_undo_operation(undo_op)
                except Exception:
                    pass

            try:
                tx.log_rollback()
            except Exception:
                pass

            self.active_transaction = None
            self._release_transaction_table_locks(locked_tables)
            raise RuntimeError(f"Transaction failed and was rolled back: {exc}") from exc

        self.active_transaction = None
        self._release_transaction_table_locks(locked_tables)
        
    def rollback_transaction(self, tx: Transaction):
        self.validate_transaction(tx)
        if len(tx.operations) > 0:
            tx.log_rollback()
        self.active_transaction = None

    def recover_from_wal(self):
        records = Transaction.read_wal_records(self.wal_path)
        if not records:
            return 0

        committed_tx_ids = {
            record.get("tx_id")
            for record in records
            if record.get("type") == "COMMIT"
        }
        rolled_back_tx_ids = {
            record.get("tx_id")
            for record in records
            if record.get("type") == "ROLLBACK"
        }
        committed_tx_ids -= rolled_back_tx_ids

        applied = 0
        self._replaying_wal = True
        try:
            for record in records:
                rec_type = record.get("type")

                if rec_type == "DDL":
                    action = record.get("action")
                    if action == "CREATE_TABLE":
                        table_name = record.get("name")
                        if table_name in self.tables:
                            continue
                        self.create_table(
                            name=table_name,
                            columns=record.get("columns", []),
                            primary_key=record.get("primary_key"),
                            indexer=record.get("indexer", "bplus"),
                            degree=record.get("degree", 4),
                            foreign_keys=record.get("foreign_keys"),
                        )
                    elif action == "DROP_TABLE":
                        table_name = record.get("name")
                        if table_name in self.tables:
                            super().drop_table(table_name)
                    continue

                if rec_type != "OP":
                    continue

                tx_id = record.get("tx_id")
                if tx_id not in committed_tx_ids:
                    continue

                op = Transaction_operation.from_wal_record(record)
                if op.table_name not in self.tables:
                    continue

                self.apply_operation(op)
                applied += 1
        finally:
            self._replaying_wal = False

        return applied

    def commit(self, tx: Optional[Transaction] = None):
        tx = tx if tx is not None else self.active_transaction
        self.commit_transaction(tx)

    def rollback(self, tx: Optional[Transaction] = None):
        tx = tx if tx is not None else self.active_transaction
        self.rollback_transaction(tx)

class DatabaseManager(BaseDatabaseManager):
    def create_database(self, db_name: str, recover: bool = False):
        if db_name in self.databases:
            raise ValueError(f"Database with name {db_name} already exists")
        self.databases[db_name] = Database(db_name=db_name)
        if recover:
            self.databases[db_name].recover_from_wal()
        return self.databases[db_name]