from .db_manager import Database
from typing import Dict, Any, List

class Transaction_Log_entry:
	def __init__(self, table_name: str, operation: str, data: Dict[str, Any]):
		self.table_name = table_name
		self.operation = operation
		self.data = data
		self.previous_state = None 
  
	def set_previous_state(self, state: Dict[str, Any]):
		self.previous_state = state
  
	def apply(self, db: Database):
		table = db.get_table(self.table_name)
		try:
			if self.operation == "insert":
				table.insert_row(self.data)
			elif self.operation == "update":
				key = self.data["key"]
				new_data = self.data["new_data"]
				existing = table.select(key)
				if existing:
					self.set_previous_state(existing)
					table.update_row(key, new_data)
				else:
					print(f"Error: Attempting to update non-existent key {key} in table {self.table_name}")
					return False
			elif self.operation == "delete":
				key = self.data["key"]
				existing = table.select(key)
				if existing:
					self.set_previous_state(existing)
					table.delete_row(key)
				else:
					print(f"Error: Attempting to delete non-existent key {key} from table {self.table_name}")
					return False
			return True
		except Exception as e:
			print(f"Error applying operation {self.operation} on table {self.table_name}: {e}")
			return False
	
	def rollback(self, db: Database):
		if self.previous_state is None:
			return
		table = db.get_table(self.table_name)
		if self.operation == "insert":
			table.delete_row(self.data[table.primary_key])
		elif self.operation == "update":
			key = self.data["key"]
			table.update_row(key, self.previous_state)
		elif self.operation == "delete":
			table.insert_row(self.previous_state)

class Transaction:
	def __init__(self, db: Database):
		self.db: Database = db
		self.operations: List[Transaction_Log_entry] = []

	def log_operation(self, table_name: str, operation: str, data: Dict[str, Any]):
		self.operations.append(Transaction_Log_entry(table_name, operation, data))
	
	def commit(self):
		for op in self.operations:
			if not op.apply(self.db):
				self.rollback()
				print("Transaction failed and rolled back")
				return
		self.operations.clear()
	
	def rollback(self):
		for op in reversed(self.operations):
			op.rollback(self.db)
		self.operations.clear()