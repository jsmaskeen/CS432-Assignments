# Indexing Benchmark Workflow (Plug-in)

## 1) Baseline run (without extra indexes)
1. Reset DB to clean state.
2. Seed the same dataset size each run.
3. Run profiler and keep baseline copy.

Commands:

```bash
cd ..
./clean_database.sh
cd backend && python3 seed_db_massive.py
cd ../profiling && python3 profile_apis.py
cp profiling_results.json profiling_results_before.json
cp profiling_results.md profiling_results_before.md
```

## 2) Apply plug-in indexes

```bash
cd ..
set -a && source backend/.env && set +a
export MYSQL_PWD="$MYSQL_PASSWORD"
mysql -u"$MYSQL_USER" cabSharing < profiling/indexes_apply.sql
```

## 3) Run profilers again (after indexing)

```bash
cd ../profiling
python3 profile_apis.py
cp profiling_results.json profiling_results_after.json
cp profiling_results.md profiling_results_after.md
```

## 4) Auto-compare before vs after

```bash
cd ../profiling
python3 compare_profiling_results.py \
  --before profiling_results_before.json \
  --after profiling_results_after.json \
  --out profiling_comparison.md
```

## 5) Capture SQL plan evidence (EXPLAIN)
Run these both before and after indexes and include in report:

```sql
EXPLAIN SELECT *
FROM Rides
WHERE Ride_Status = 'Open'
ORDER BY Departure_Time ASC
LIMIT 100;

EXPLAIN SELECT *
FROM Bookings
WHERE RideID = 123 AND Booking_Status = 'Pending'
ORDER BY Booked_At DESC;

EXPLAIN SELECT *
FROM Bookings
WHERE Passenger_MemberID = 1001
ORDER BY Booked_At DESC;

EXPLAIN SELECT *
FROM Reputation_Reviews
WHERE RideID = 123
ORDER BY Created_At DESC;
```

## 6) Rollback indexes (optional)

```bash
cd ..
set -a && source backend/.env && set +a
export MYSQL_PWD="$MYSQL_PASSWORD"
mysql -u"$MYSQL_USER" cabSharing < profiling/indexes_drop.sql
```
