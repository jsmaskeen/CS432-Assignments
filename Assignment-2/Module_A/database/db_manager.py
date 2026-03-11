from database.table import Table
from typing import List, Dict, Literal


class DatabaseManager:
    def __init__(self):
        self.tables: Dict[str, Table] = {}

    def create_table(
        self,
        name: str,
        columns: List[str],
        primary_key: str,
        indexer: Literal["brute", "bplus"] = "bplus",
        degree: int = 4,
    ):
        if name in self.tables:
            raise ValueError(f"Table '{name}' already exists")
        self.tables[name] = Table(name, columns, primary_key, indexer, degree)
        return self.tables[name]

    def drop_table(self, name: str):
        if name not in self.tables:
            raise ValueError(f"Table '{name}' does not exist")
        del self.tables[name]

    def get_table(self, name: str):
        if name not in self.tables:
            raise ValueError(f"Table '{name}' does not exist")
        return self.tables[name]

    def list_tables(self):
        return list(self.tables.keys())

    def __repr__(self):
        return f"DatabaseManager(tables={self.list_tables()})"
