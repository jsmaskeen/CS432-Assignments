from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional

class Transaction_operation:
    def __init__(self, action: Literal["insert", "update", "delete"], table_name: str, key: int, row: Optional[Dict[str, Any]] = None):
        self.action = action
        self.table_name = table_name
        self.key = key
        self.row = row


class Transaction:
    def __init__(self, db):
        self.db = db
        self.operations: List[Transaction_operation] = []
        self.staged_rows: Dict[str, Dict[int, Optional[Dict[str, Any]]]] = {}

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
        cur_row = deepcopy(row)
        self.operations.append(Transaction_operation("insert", table_name, key, cur_row))
        self.staged_rows.setdefault(table_name, {})[key] = cur_row

    def stage_update(self, table_name: str, key: int, row: Dict[str, Any]):
        cur_row = deepcopy(row)
        self.operations.append(Transaction_operation("update", table_name, key, cur_row))
        self.staged_rows.setdefault(table_name, {})[key] = cur_row

    def stage_delete(self, table_name: str, key: int):
        table_rows = self.staged_rows.setdefault(table_name, {})
        if key in table_rows and table_rows[key] is None:
            return

        self.operations.append(Transaction_operation("delete", table_name, key, None))
        table_rows[key] = None

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