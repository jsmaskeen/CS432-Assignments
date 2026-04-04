import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager


class TestAtomicityWithContextManager(unittest.TestCase):
    def setUp(self):
        self.db_manager = DatabaseManager()
        self.db = self.db_manager.create_database("test_atomicity_db")

        self.db.create_table(
            name="Accounts",
            columns=["account_id", "owner", "balance"],
            primary_key="account_id",
            integrity_checks=[
                {"column": "owner", "not_null": True},
                {"column": "balance", "not_null": True, "check": lambda value: value >= 0, "message": "balance must be >= 0"},
            ],
        )

        accounts = self.db.get_table("Accounts")
        accounts.insert_row({"account_id": 1, "owner": "Alice", "balance": 100})

    # Verifies atomic success: all valid statements inside the context manager are committed together.
    def test_context_manager_commits_all_when_no_error(self):
        accounts = self.db.get_table("Accounts")

        with self.db.begin_transaction() as tx:
            accounts.insert_row({"account_id": 2, "owner": "Bob", "balance": 80}, tx=tx)
            accounts.update_row(1, {"balance": 70}, tx=tx)

        self.assertEqual(accounts.select(1)["balance"], 70)
        self.assertIsNotNone(accounts.select(2))

    # Verifies atomic failure: if one statement fails, the context manager rolls back the entire transaction.
    def test_context_manager_rolls_back_all_when_error_occurs(self):
        accounts = self.db.get_table("Accounts")

        with self.assertRaises(ValueError):
            with self.db.begin_transaction() as tx:
                accounts.insert_row({"account_id": 3, "owner": "Charlie", "balance": 50}, tx=tx)
                accounts.update_row(1, {"balance": -10}, tx=tx)

        # The valid insert above must also be absent because the whole transaction is rolled back.
        self.assertIsNone(accounts.select(3))
        self.assertEqual(accounts.select(1)["balance"], 100)

    def tearDown(self):
        self.db_manager.delete_database("test_atomicity_db")


if __name__ == "__main__":
    unittest.main()
