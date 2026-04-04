
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

from .transaction import Transaction
from .table import Table
from typing import List, Dict, Any, Literal, Optional

class Database(BaseDatabase):
    def __init__(self):
        super().__init__()
        self.in_transaction = False
        self.current_transaction = None
    
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
    
    def begin_transaction(self):
        if self.in_transaction:
            raise RuntimeError("Transaction already in progress")
        self.in_transaction = True
        self.current_transaction = Transaction(self)
        
    def commit_transaction(self):
        if not self.in_transaction:
            raise RuntimeError("No transaction in progress")
        self.current_transaction.commit()
        self.in_transaction = False
        
    def rollback_transaction(self):
        if not self.in_transaction:
            raise RuntimeError("No transaction in progress")
        self.current_transaction.rollback()
        self.in_transaction = False
        
    def insert_tx_opt(self, table_name: str, operation: str, data: Dict[str, Any]):
        if not self.in_transaction:
            raise RuntimeError("No transaction in progress")
        self.current_transaction.log_operation(table_name, operation, data)

class DatabaseManager(BaseDatabaseManager):
    def create_database(self, db_name: str):
        if db_name in self.databases:
            raise ValueError(f"Database with name {db_name} already exists")
        self.databases[db_name] = Database()
        return self.databases[db_name]

