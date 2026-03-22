from database.table import Table
from typing import List, Dict, Literal


class Database:
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
        return f"Database(tables={self.list_tables()})"

class DatabaseManager:
    def __init__(self):
        self.databases: Dict[str, Database] = {}

    def create_database(self, db_name: str):
        if db_name in self.databases:
            raise ValueError(f"Database with name {db_name} already exists")
        self.databases[db_name] = Database()
        return self.databases[db_name]

    def delete_database(self, db_name: str):
        if db_name not in self.databases:
            return False
        self.databases.pop(db_name)
        return True

    def list_databases(self):
        return list(self.databases.keys())

    def get_database(self,db_name:str):
        if db_name not in self.databases.keys():
            raise ValueError(f"Database with name {db_name} does not exists")
        return self.databases[db_name]
    
    def __repr__(self):
        return f"DatabaseManager(databases={self.list_databases()})"

