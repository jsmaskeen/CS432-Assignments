import os
import subprocess
import sys
import tempfile
import threading
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager


class TestAdditionalACIDScenarios(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_additional_acid_db"
        self.db_manager = DatabaseManager()
        self.db = self.db_manager.create_database(self.db_name)

        self.db.create_table(
            name="Members",
            columns=[
                "MemberID",
                "OAUTH_TOKEN",
                "Email",
                "Full_Name",
                "Reputation_Score",
                "Phone_Number",
                "Created_At",
                "Gender",
            ],
            primary_key="MemberID",
            integrity_checks=[
                {"column": "OAUTH_TOKEN", "not_null": True},
                {"column": "Email", "not_null": True, "check": lambda value: value.endswith("@iitgn.ac.in")},
                {"column": "Full_Name", "not_null": True},
                {"column": "Reputation_Score", "not_null": True, "check": lambda value: 0.0 <= value <= 5.0},
                {"column": "Gender", "not_null": True, "check": lambda value: value in {"Male", "Female", "Other"}},
            ],
        )

        members = self.db.get_table("Members")
        members.insert_row(
            {
                "MemberID": 1,
                "OAUTH_TOKEN": "tok_alice",
                "Email": "alice@iitgn.ac.in",
                "Full_Name": "Alice",
                "Reputation_Score": 4.7,
                "Phone_Number": "9999999999",
                "Created_At": "2026-01-01 10:00:00",
                "Gender": "Female",
            }
        )

    # Verifies crash recovery replays only committed operations and ignores incomplete transactions.
    def test_recovery_replays_only_committed_transactions_after_crash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wal_path = os.path.join(temp_dir, "recovery_only_committed.wal.jsonl")
            db_name = "recovery_subprocess_db"

            crash_script = """
import os
import sys
from database.db_manager import DatabaseManager

wal_path = sys.argv[1]
db_name = sys.argv[2]

db_manager = DatabaseManager()
db = db_manager.create_database(db_name)
db.set_wal_path(wal_path)

db.create_table(
    name="Members",
    columns=["MemberID", "OAUTH_TOKEN", "Email", "Full_Name", "Reputation_Score", "Phone_Number", "Created_At", "Gender"],
    primary_key="MemberID",
    integrity_checks=[
        {"column": "OAUTH_TOKEN", "not_null": True},
        {"column": "Email", "not_null": True, "check": lambda value: value.endswith("@iitgn.ac.in")},
        {"column": "Full_Name", "not_null": True},
        {"column": "Reputation_Score", "not_null": True, "check": lambda value: 0.0 <= value <= 5.0},
        {"column": "Gender", "not_null": True, "check": lambda value: value in {"Male", "Female", "Other"}},
    ],
)

members = db.get_table("Members")

tx1 = db.begin_transaction()
members.insert_row(
    {
        "MemberID": 101,
        "OAUTH_TOKEN": "tok_committed",
        "Email": "committed@iitgn.ac.in",
        "Full_Name": "Committed",
        "Reputation_Score": 4.1,
        "Phone_Number": "7000000001",
        "Created_At": "2026-01-10 10:00:00",
        "Gender": "Other",
    },
    tx=tx1,
)
db.commit(tx1)

# Intentionally leave this transaction without commit to emulate crash-loss.
tx2 = db.begin_transaction()
members.insert_row(
    {
        "MemberID": 102,
        "OAUTH_TOKEN": "tok_uncommitted",
        "Email": "uncommitted@iitgn.ac.in",
        "Full_Name": "Uncommitted",
        "Reputation_Score": 4.2,
        "Phone_Number": "7000000002",
        "Created_At": "2026-01-10 10:01:00",
        "Gender": "Female",
    },
    tx=tx2,
)

os._exit(1)
""".strip()

            env = os.environ.copy()
            env["PYTHONPATH"] = BASE_DIR + os.pathsep + env.get("PYTHONPATH", "")
            subprocess.run(
                [sys.executable, "-c", crash_script, wal_path, db_name],
                check=False,
                cwd=BASE_DIR,
                env=env,
            )

            recovery_manager = DatabaseManager()
            recovered_db = recovery_manager.create_database("recovered_db")
            recovered_db.set_wal_path(wal_path)
            applied = recovered_db.recover_from_wal()

            recovered_members = recovered_db.get_table("Members")
            self.assertEqual(applied, 1)
            self.assertIsNotNone(recovered_members.select(101))
            self.assertIsNone(recovered_members.select(102))

            recovery_manager.delete_database("recovered_db")

    # Verifies duplicate-PK failure at commit rolls back every staged write in the transaction.
    def test_duplicate_primary_key_in_tx_rolls_back_all_staged_rows(self):
        members = self.db.get_table("Members")

        with self.assertRaises(RuntimeError):
            with self.db.begin_transaction() as tx:
                members.insert_row(
                    {
                        "MemberID": 10,
                        "OAUTH_TOKEN": "tok_one",
                        "Email": "one@iitgn.ac.in",
                        "Full_Name": "One",
                        "Reputation_Score": 4.0,
                        "Phone_Number": "8111111111",
                        "Created_At": "2026-02-01 10:00:00",
                        "Gender": "Male",
                    },
                    tx=tx,
                )
                members.insert_row(
                    {
                        "MemberID": 11,
                        "OAUTH_TOKEN": "tok_two",
                        "Email": "two@iitgn.ac.in",
                        "Full_Name": "Two",
                        "Reputation_Score": 4.1,
                        "Phone_Number": "8222222222",
                        "Created_At": "2026-02-01 10:01:00",
                        "Gender": "Female",
                    },
                    tx=tx,
                )
                # Duplicate key in same transaction should force rollback of the full batch.
                members.insert_row(
                    {
                        "MemberID": 10,
                        "OAUTH_TOKEN": "tok_dup",
                        "Email": "dup@iitgn.ac.in",
                        "Full_Name": "Duplicate",
                        "Reputation_Score": 4.3,
                        "Phone_Number": "8333333333",
                        "Created_At": "2026-02-01 10:02:00",
                        "Gender": "Other",
                    },
                    tx=tx,
                )

        self.assertIsNone(members.select(10))
        self.assertIsNone(members.select(11))
        self.assertIsNotNone(members.select(1))

    # Verifies rollback path remains atomic for a large transaction payload.
    def test_large_transaction_rollback_leaves_no_partial_rows(self):
        members = self.db.get_table("Members")

        with self.assertRaises(RuntimeError):
            with self.db.begin_transaction() as tx:
                for member_id in range(1000, 1300):
                    members.insert_row(
                        {
                            "MemberID": member_id,
                            "OAUTH_TOKEN": f"tok_{member_id}",
                            "Email": f"u{member_id}@iitgn.ac.in",
                            "Full_Name": f"User {member_id}",
                            "Reputation_Score": 4.0,
                            "Phone_Number": f"9{member_id:09d}"[-10:],
                            "Created_At": "2026-03-01 10:00:00",
                            "Gender": "Other",
                        },
                        tx=tx,
                    )

                members.insert_row(
                    {
                        "MemberID": 1000,
                        "OAUTH_TOKEN": "tok_conflict",
                        "Email": "conflict@iitgn.ac.in",
                        "Full_Name": "Conflict",
                        "Reputation_Score": 3.9,
                        "Phone_Number": "9555555555",
                        "Created_At": "2026-03-01 10:01:00",
                        "Gender": "Male",
                    },
                    tx=tx,
                )

        self.assertEqual(len(members.select_range(1000, 1300)), 0)

    # Verifies write-write conflict semantics on the same row under concurrent transactions.
    # @unittest.expectedFailure
    def test_concurrent_same_row_updates_do_not_allow_two_successful_commits(self):
        members = self.db.get_table("Members")

        start_commit = threading.Event()
        finished = threading.Event()
        results = []

        def worker(member_score):
            try:
                with self.db.begin_transaction() as tx:
                    members.update_row(1, {"Reputation_Score": member_score}, tx=tx)
                    start_commit.wait(timeout=2)
                results.append("commit")
            except Exception:
                results.append("fail")
            finally:
                if len(results) == 2:
                    finished.set()

        t1 = threading.Thread(target=worker, args=(4.1,))
        t2 = threading.Thread(target=worker, args=(4.3,))

        t1.start()
        t2.start()

        start_commit.set()
        finished.wait(timeout=3)

        t1.join(timeout=2)
        t2.join(timeout=2)

        # Strict isolation expectation: at most one writer should successfully commit.
        self.assertLessEqual(results.count("commit"), 1)
        self.assertIn(members.select(1)["Reputation_Score"], {4.1, 4.3, 4.7})

    def tearDown(self):
        self.db_manager.delete_database(self.db_name)


if __name__ == "__main__":
    unittest.main()
