
import sys
import os
import importlib.util
from threading import RLock

ASSN2_MODULE_A = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Assignment-2/Module_A"))

assn2_table_path = os.path.join(ASSN2_MODULE_A, "database", "table.py")
spec = importlib.util.spec_from_file_location("assn2_database.table", assn2_table_path)
assn2_table = importlib.util.module_from_spec(spec)
sys.modules["assn2_database.table"] = assn2_table
spec.loader.exec_module(assn2_table)

BaseTable = assn2_table.Table

from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .db_manager import Database
    from .transaction import Transaction

class Table(BaseTable):
    def __init__(
        self,
        name: str,
        columns: List[str],
        primary_key: str,
        foreign_keys: Optional[List[Dict[str, Any]]] = None,
        integrity_checks: Optional[List[Dict[str, Any]]] = None,
        db_manager: "Database" = None,
        **kwargs,
    ):
        super().__init__(name, columns, primary_key, **kwargs)
        self.foreign_keys = foreign_keys if foreign_keys else []
        self.integrity_checks = integrity_checks if integrity_checks else []
        self.db_manager = db_manager
        self._table_lock = RLock()
        self._validate_integrity_checks()

    def _validate_integrity_checks(self):
        for check in self.integrity_checks:
            column = check.get("column")
            if column not in self.columns:
                raise ValueError(f"Integrity check column '{column}' does not exist in table {self.name}")

            if "check" in check and not callable(check["check"]):
                raise ValueError(f"Integrity CHECK for column '{column}' must be callable")

    def _run_integrity_checks(self, row: Dict[str, Any]):
        for check in self.integrity_checks:
            column = check["column"]
            value = row.get(column)

            if check.get("not_null") and value is None:
                raise ValueError(f"NOT NULL constraint failed: {self.name}.{column}")

            predicate = check.get("check")
            if predicate is None:
                continue

            try:
                is_valid = predicate(value, row)
            except TypeError:
                is_valid = predicate(value)

            if not is_valid:
                message = check.get("message") or f"CHECK constraint failed: {self.name}.{column}"
                raise ValueError(message)

    def acquire_table_lock(self, blocking: bool = True, timeout: float = -1):
        return self._table_lock.acquire(blocking, timeout)

    def release_table_lock(self):
        self._table_lock.release()

    def _apply_insert_direct(self, row: Dict[str, Any]):
        super().insert_row(row)

    def _apply_update_direct(self, key: int, row: Dict[str, Any]):
        return super().update_row(key, row)

    def _apply_delete_direct(self, key: int):
        return super().delete_row(key)

    def _check_foreign_key(self, row: Dict[str, Any], tx: Optional["Transaction"] = None):
        if not self.db_manager:
            return 

        for fk in self.foreign_keys:
            foreign_key_value = row.get(fk['column'])
            if foreign_key_value is None:
                continue

            referenced_table = self.db_manager.get_table(fk['references_table'])
            if referenced_table.select(foreign_key_value, tx=tx) is None:      
                raise ValueError(f"Foreign key constraint failed: value {foreign_key_value} not found in {fk['references_table']}({fk['references_column']})")
            
    def select(self, key: int, tx: Optional["Transaction"] = None):
        with self._table_lock:
            if tx is not None:
                found, staged_row = tx.staged_lookup(self.name, key)
                if found:
                    return staged_row
            return super().select(key)

    def select_all(self, tx: Optional["Transaction"] = None):
        with self._table_lock:
            if tx is None:
                return super().select_all()

            merged_rows = {row[self.primary_key]: row for row in super().select_all()}
            for key, row in tx.staged_rows_for_table(self.name).items():
                if row is None:
                    merged_rows.pop(key, None)
                else:
                    merged_rows[key] = row

            return [merged_rows[key] for key in sorted(merged_rows.keys())]

    def select_range(self, start_key: int, end_key: int, tx: Optional["Transaction"] = None):
        with self._table_lock:
            if tx is None:
                return super().select_range(start_key, end_key)

            rows = [
                row
                for row in self.select_all(tx=tx)
                if start_key <= row[self.primary_key] <= end_key
            ]
            rows.sort(key=lambda row: row[self.primary_key])
            return rows

    def insert_row(self, row: Dict[str, Any], tx: Optional["Transaction"] = None):
        if tx is None and self.db_manager is not None:
            if self.db_manager.active_transaction is None:
                return self.db_manager.run_autocommit(lambda implicit_tx: self.insert_row(row, tx=implicit_tx))
            tx = self.db_manager.active_transaction

        with self._table_lock:
            self._run_integrity_checks(row)
            self._check_foreign_key(row, tx=tx)

            if tx is None:
                self._apply_insert_direct(row)
                return

            tx.stage_insert(self.name, row[self.primary_key], row)
        
    def update_row(self, key: int, new_data: Dict[str, Any], tx: Optional["Transaction"] = None):
        if tx is None and self.db_manager is not None:
            if self.db_manager.active_transaction is None:
                return self.db_manager.run_autocommit(lambda implicit_tx: self.update_row(key, new_data, tx=implicit_tx))
            tx = self.db_manager.active_transaction

        with self._table_lock:
            existing = self.select(key, tx=tx)
            if not existing:
                return False

            updated_row = {**existing, **new_data}
            self._run_integrity_checks(updated_row)
            self._check_foreign_key(updated_row, tx=tx)

            if tx is None:
                return self._apply_update_direct(key, new_data)

            tx.stage_update(self.name, key, updated_row)
            return True
    
    def delete_row(self, key: int, tx: Optional["Transaction"] = None):
        if tx is None and self.db_manager is not None:
            if self.db_manager.active_transaction is None:
                return self.db_manager.run_autocommit(lambda implicit_tx: self.delete_row(key, tx=implicit_tx))
            tx = self.db_manager.active_transaction

        with self._table_lock:
            if not self.db_manager:
                if tx is None:
                    return self._apply_delete_direct(key)
                tx.stage_delete(self.name, key)
                return True

            for table in self.db_manager.tables.values():
                if table.foreign_keys:
                    for fk in table.foreign_keys:
                        if fk['references_table'] == self.name:
                            all_rows = table.select_all(tx=tx)
                            keys_to_delete = []
                            for row in all_rows:
                                if row.get(fk['column']) == key:
                                    if fk.get('on_delete', 'RESTRICT').upper() == 'CASCADE':
                                        keys_to_delete.append(row[table.primary_key])
                                    else:
                                        raise ValueError(f"Cannot delete row with key {key} from table {self.name} because it is referenced by table {table.name}")
                            
                            for k in keys_to_delete:
                                table.delete_row(k, tx=tx)

            if tx is None:
                return self._apply_delete_direct(key)

            tx.stage_delete(self.name, key)
            return True