# ACID Test Summary (Assignment-3 / Module_A)

This document summarizes ACID coverage with one dedicated file per ACID property.

## Test Organization

- Atomicity: `tests/test_atomicity_context_manager.py`
- Consistency: `tests/test_consistency.py`
- Isolation: `tests/test_isolation_acid.py`
- Durability: `tests/test_durability_acid.py`

## Atomicity

### Test File

- `tests/test_atomicity_context_manager.py`

### Covered Tests

- `test_context_manager_commits_all_when_no_error`
	- Commits a valid multi-step transaction and verifies all changes are persisted.
- `test_context_manager_rolls_back_all_when_error_occurs`
	- Triggers a failing statement inside the transaction and verifies all staged work is rolled back.
- `test_context_manager_rolls_back_all_on_mid_transaction_signal`
	- Raises a signal after one staged operation to simulate interruption in the middle, then verifies full rollback.
- `test_power_failure_mid_transaction_has_no_committed_operations`
	- Uses a subprocess with `os._exit(1)` before commit and verifies WAL has no committed operations.

### What These Tests Show

- A successful transaction commits all staged operations together.
- If any statement fails, the transaction is rolled back as a unit.
- A signal-triggered interruption mid-transaction does not leak partial writes.
- A power-failure style hard exit before commit does not leave committed WAL state.

### Practical Note

- Use `with db.begin_transaction() as tx` to get automatic rollback on exceptions.

## Consistency

### Test File

- `tests/test_consistency.py`

### Covered Tests

- `test_valid_chain_insert_succeeds`
	- Inserts valid rows across `Members`, `Rides`, and `Bookings` and verifies acceptance.
- `test_member_constraints_reject_invalid_values`
	- Verifies member NOT NULL, domain, and range checks reject invalid rows.
- `test_ride_cross_column_constraints_reject_invalid_values`
	- Verifies cross-column checks on rides reject inconsistent seat/geohash combinations.
- `test_foreign_key_constraints_reject_missing_references`
	- Verifies FK checks reject missing parent references for rides/bookings.

### What These Tests Show

- Valid data is accepted.
- NOT NULL and CHECK constraints are enforced.
- Foreign-key constraints are enforced.

### Practical Note

- Constraints are validated when statements run, before staging in a transaction and also again when the actual statement is run.

## Isolation

### Test File

- `tests/test_isolation_acid.py`

### Covered Tests

- `test_uncommitted_insert_not_visible_outside_transaction`
	- Verifies staged inserts are hidden from non-transactional reads.
- `test_uncommitted_update_not_visible_outside_transaction`
	- Verifies staged updates are hidden from non-transactional reads.
- `test_uncommitted_delete_not_visible_outside_transaction`
	- Verifies staged deletes are hidden from non-transactional reads.
- `test_tx_select_all_and_range_reflect_staged_state_only`
	- Verifies tx-aware full/range reads include staged rows while external reads do not.
- `test_concurrent_reader_cannot_see_uncommitted_update`
	- Verifies a concurrent reader thread observes committed state while another transaction has uncommitted updates.
- `test_second_transaction_in_same_thread_is_rejected`
	- Verifies a second transaction cannot start while one is already active in the same thread.
- `test_concurrent_transactions_across_threads_can_both_commit`
	- Verifies two transactions can exist simultaneously in different threads and both commit successfully.

### What These Tests Show

- Uncommitted changes are visible only via transaction-aware reads.
- Non-transaction reads continue to see committed state.
- Transaction-aware `select_all` and `select_range` include staged rows.
- The implementation allows one active transaction per thread and multiple active transactions across threads.

### Practical Note

- If one transaction is already active in the current thread, another `begin_transaction()` call will raise.

## Durability

### Test File

- `tests/test_durability_acid.py`

### Covered Tests

- `test_committed_data_persists_across_follow_up_transactions`
	- Verifies committed changes remain available across subsequent transaction boundaries.
- `test_wal_contains_commit_record_after_successful_commit`
	- Verifies WAL contains `BEGIN`, `OP`, and `COMMIT` records after a successful commit.
- `test_power_failure_before_commit_keeps_wal_uncommitted`
	- Simulates power failure via `os._exit(1)` before commit and verifies WAL has no committed operations.
- `test_power_failure_after_commit_preserves_committed_wal_state`
	- Simulates power failure via `os._exit(1)` after commit and verifies committed WAL operations are preserved.
- `test_sigint_inside_transaction_rolls_back_uncommitted_changes`
	- Verifies signal interruption during a transaction does not leave partial writes.
- `test_sigint_after_commit_preserves_committed_state`
	- Verifies signal interruption after commit does not affect committed rows.

### What These Tests Show

- Committed data remains available in later operations.
- Power failure before commit leaves no committed WAL operations, while power failure after commit preserves committed WAL operations.
- Signal interruption during an open transaction does not leave partial writes.
- Signal interruption after commit keeps committed rows intact.

### Practical Note

- Signal-based tests use `SIGUSR1` with a controlled handler to model interrupt behavior safely in the test runner.

## Related Coverage

- `tests/test_integrity_checks.py` adds broader integrity and transaction interaction scenarios.
- `tests/test_foreign_keys.py` adds broader foreign-key and cascade scenarios.
