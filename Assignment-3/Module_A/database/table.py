
import sys
import os
import importlib.util

ASSN2_MODULE_A = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Assignment-2/Module_A"))

assn2_table_path = os.path.join(ASSN2_MODULE_A, "database", "table.py")
spec = importlib.util.spec_from_file_location("assn2_database.table", assn2_table_path)
assn2_table = importlib.util.module_from_spec(spec)
sys.modules["assn2_database.table"] = assn2_table
spec.loader.exec_module(assn2_table)

BaseTable = assn2_table.Table

from .db_manager import Database
from typing import List, Dict, Any, Optional

class Table(BaseTable):
    def __init__(self, name: str, columns: List[str], primary_key: str, foreign_keys: Optional[List[Dict[str, Any]]] = None, db_manager: Database=None, **kwargs):
        super().__init__(name, columns, primary_key, **kwargs)
        self.foreign_keys = foreign_keys if foreign_keys else []
        self.db_manager = db_manager

    def _check_foreign_key(self, row: Dict[str, Any]):
        if not self.db_manager:
            return 

        for fk in self.foreign_keys:
            foreign_key_value = row.get(fk['column'])
            if foreign_key_value is None:
                continue

            referenced_table = self.db_manager.get_table(fk['references_table'])
            if referenced_table.select(foreign_key_value) is None:
                raise ValueError(f"Foreign key constraint failed: value {foreign_key_value} not found in {fk['references_table']}({fk['references_column']})")

    def insert_row(self, row: Dict[str, Any]):
        if self.db_manager.in_transaction:
            self.db_manager.insert_tx_opt(self.name, "insert", row)
        self._check_foreign_key(row)
        super().insert_row(row)

    def update_row(self, key: int, new_data: Dict[str, Any]):
        if self.db_manager.in_transaction:
            self.db_manager.insert_tx_opt(self.name, "update", {"key": key, "new_data": new_data})
        
        existing = self.select(key)
        if not existing:
            return False
        
        updated_row = {**existing, **new_data}
        self._check_foreign_key(updated_row)
        return super().update_row(key, new_data)

    def delete_row(self, key: int):
        if self.db_manager.in_transaction:
            self.db_manager.insert_tx_opt(self.name, "delete", {"key": key})
        
        if not self.db_manager:
            return super().delete_row(key)

        for table in self.db_manager.tables.values():
            if table.foreign_keys:
                for fk in table.foreign_keys:
                    if fk['references_table'] == self.name:
                        all_rows = table.select_all()
                        keys_to_delete = []
                        for row in all_rows:
                            if row.get(fk['column']) == key:
                                if fk.get('on_delete', 'RESTRICT').upper() == 'CASCADE':
                                    keys_to_delete.append(row[table.primary_key])
                                else:
                                    raise ValueError(f"Cannot delete row with key {key} from table {self.name} because it is referenced by table {table.name}")
                        
                        for k in keys_to_delete:
                            table.delete_row(k)
        
        return super().delete_row(key)
