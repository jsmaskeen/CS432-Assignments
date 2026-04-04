
import sys
import os
import importlib.util
from copy import deepcopy

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
    def __init__(self):
        super().__init__()
        self.active_transaction: Union[Transaction, None] = None
    
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
        return self.tables[name]
    
    def begin_transaction(self):
        if self.active_transaction is not None:
            raise ValueError(f"Cannot begin a new transaction while transaction {self.active_transaction} is active")
        self.active_transaction = Transaction(self)
        return self.active_transaction

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

    def apply_operation(self, op: Transaction_operation, undo_log: List[Transaction_operation]):
        table = self.get_table(op.table_name)
        
        if op.action == "insert":
            if op.row is None:
                raise ValueError("Corrupt transaction operation: missing row for insert")
            if table.select(op.key) is not None:
                raise ValueError(f"Duplicate primary key: {op.key}")
            table.insert_row(op.row)
            undo_log.append(Transaction_operation("delete", op.table_name, op.key))
            return

        if op.action == "update":
            if op.row is None:
                raise ValueError("Corrupt transaction operation: missing row for update")
            previous = table.select(op.key)
            if previous is None:
                raise ValueError(f"Cannot update missing key {op.key} in table {op.table_name}")
            table.update_row(op.key, op.row)
            undo_log.append(Transaction_operation("update", op.table_name, op.key, deepcopy(previous)))
            return

        if op.action == "delete":
            previous = table.select(op.key)
            if previous is None:
                raise ValueError(f"Cannot delete missing key {op.key} from table {op.table_name}")
            table.delete_row(op.key)
            undo_log.append(Transaction_operation("insert", op.table_name, op.key, deepcopy(previous)))
            return

        raise ValueError(f"Unsupported transaction action: {op.action}")

    def apply_undo_operation(self, op: Transaction_operation):
        table = self.get_table(op.table_name)
        if op.action == "insert":
            if op.row is None:
                raise ValueError("Corrupt undo operation: missing row for insert")
            table.insert_row(op.row)
            return
        if op.action == "update":
            if op.row is None:
                raise ValueError("Corrupt undo operation: missing row for update")
            table.update_row(op.key, op.row)
            return
        if op.action == "delete":
            table.delete_row(op.key)
            return
        raise ValueError(f"Unsupported undo action: {op.action}")
        
    def commit_transaction(self, tx: Transaction):
        self.validate_transaction(tx)
        undo_log: List[Transaction_operation] = []
        locked_tables = self._acquire_transaction_table_locks(tx)

        try:
            for op in tx.operations:
                self.apply_operation(op, undo_log)

        except Exception as exc:
            for undo_op in reversed(undo_log):
                try:
                    self.apply_undo_operation(undo_op)
                except Exception:
                    pass

            self.active_transaction = None
            self._release_transaction_table_locks(locked_tables)
            raise RuntimeError(f"Transaction failed and was rolled back: {exc}") from exc

        self.active_transaction = None
        self._release_transaction_table_locks(locked_tables)
        
    def rollback_transaction(self, tx: Transaction):
        self.validate_transaction(tx)
        self.active_transaction = None

    def commit(self, tx: Optional[Transaction] = None):
        tx = tx if tx is not None else self.active_transaction
        self.commit_transaction(tx)

    def rollback(self, tx: Optional[Transaction] = None):
        tx = tx if tx is not None else self.active_transaction
        self.rollback_transaction(tx)

class DatabaseManager(BaseDatabaseManager):
    def create_database(self, db_name: str):
        if db_name in self.databases:
            raise ValueError(f"Database with name {db_name} already exists")
        self.databases[db_name] = Database()
        return self.databases[db_name]