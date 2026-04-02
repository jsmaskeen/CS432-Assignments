
import sys
import os
import importlib.util

ASSN2_MODULE_A = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Assignment-2/Module_A"))

assn2_db_mgr_path = os.path.join(ASSN2_MODULE_A, "database", "db_manager.py")
spec = importlib.util.spec_from_file_location("assn2_database.db_manager", assn2_db_mgr_path)
assn2_db_manager = importlib.util.module_from_spec(spec)
sys.modules["assn2_database.db_manager"] = assn2_db_manager
spec.loader.exec_module(assn2_db_manager)

BaseDatabase = assn2_db_manager.Database
BaseDatabaseManager = assn2_db_manager.DatabaseManager

from .table import Table
from typing import List, Dict, Any, Literal, Optional

class Database(BaseDatabase):
    def create_table(
        self,
        name: str,
        columns: List[str],
        primary_key: str,
        indexer: Literal["brute", "bplus"] = "bplus",
        degree: int = 4,
        foreign_keys: Optional[List[Dict[str, Any]]] = None,
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
            db_manager=self 
        )
        return self.tables[name]

class DatabaseManager(BaseDatabaseManager):
    def create_database(self, db_name: str):
        if db_name in self.databases:
            raise ValueError(f"Database with name {db_name} already exists")
        self.databases[db_name] = Database()
        return self.databases[db_name]

