from database.bplustree import BPlusTree
from database.bruteeforce import BruteForceDB
from typing import Literal, List, Union, Dict, Any, cast

"""
Assumptions:
- Primary key can be just a single column and is supposed to be an integer.
- We are not enforcing any checks on type of values inserted into the table as of now. May support later ? 
"""


class Table:
    def __init__(
        self,
        name: str,  # table name
        columns: List[str],  # column names
        primary_key: str,  # must be in columns
        indexer: Literal["brute", "bplus"] = "bplus",
        degree: int = 4,  # max children per node in case of Bplus tree
    ):
        if primary_key not in columns:
            raise ValueError(f"Primary key '{primary_key}' not in schema {columns}")
        self.name = name
        self.columns = columns
        self.primary_key = primary_key

        self.tree:Union[BruteForceDB,BPlusTree] = BPlusTree(primary_key=self.primary_key,degree=degree) if indexer == 'bplus' else BruteForceDB()

    def _validate_row(self, row: Any):
        if not isinstance(row, dict):
            raise TypeError("Row must be a dict")
        row = cast(Dict[str, Any], row)
        missing = set(self.columns) - set(row.keys())
        if missing:
            raise ValueError(f"Row missing columns: {missing}")

    def insert_row(self, row: Dict[str, Any]):
        self._validate_row(row)
        key: int = row[self.primary_key]
        if self.tree.search(key) is not None:
            raise ValueError(f"Duplicate primary key: {key}")
        self.tree.insert(key, row)

    def select(self, key: int):
        return self.tree.search(key)

    def select_range(self, start_key: int, end_key: int):
        return self.tree.range_query(start_key, end_key)

    def update_row(self, key: int, new_data: Dict[str, Any]):
        existing = self.tree.search(key)
        if existing is None:
            return False
        updated = {**existing, **new_data}
        updated[self.primary_key] = key
        return self.tree.update(key, updated)

    def delete_row(self, key: int):
        return self.tree.delete(key)
    
    def select_all(self):
        return self.tree.get_all()

    def __repr__(self):
        return (
            f"Table(name='{self.name}', schema={self.columns}, primary_key='{self.primary_key}')"
        )
