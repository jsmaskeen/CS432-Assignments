# TODO



- [x] Shard-key selection + quantified evidence (RideID modulo-3)
- [x] Core/Config: Shard host/port settings, URI builders
- [x] DB/Sharding: SQLAlchemy engines, session makers, context managers
- [x] Models/Shard_Directory: Persistent RideID : ShardID mapping
- [x] Scripts/Shard_key: Reproducible evidence extraction
- [x] Scripts/Migrate_Rides_To_Shards: Migration with FK fixes (Members mirrored per shard)
- [x] Scripts/Generate_Fake_Data: Realistic test data generation
- [x] Scripts/Validate_Shard_Migration: Post-migration integrity checks
- [x] API/Routes/Sharding: Demo endpoints for verification
- [x] Scripts/Cleanup_DB: Python-native DB reset without mysql CLI

Endpoints to Refactor:
- [x] Single-ride operations
  - [x] `POST /api/v1/rides` : write to shard
  - [x] `GET /api/v1/rides/{ride_id}` : read from shard
  - [x] `PATCH /api/v1/rides/{ride_id}` : write to shard
  - [x] `POST /api/v1/rides/{ride_id}/start` : write to shard
  - [x] `POST /api/v1/rides/{ride_id}/end` : write + settlements on shard
  - [x] `DELETE /api/v1/rides/{ride_id}` : delete on shard
  - [x] `GET /api/v1/rides/{ride_id}/with-bookings` : read from shard
  
- [x] Booking endpoints (core operations)
  - [x] `POST /api/v1/rides/{ride_id}/book` : write to shard
  - [x] `DELETE /api/v1/bookings/{booking_id}` : resolve via Rides.RideID : shard
  - [x] `POST /api/v1/bookings/{booking_id}/accept` : resolve via Rides.RideID : shard
  - [x] `POST /api/v1/bookings/{booking_id}/reject` : resolve via Rides.RideID : shard
  
- [ ] Chat endpoints
  - [ ] `POST /api/v1/rides/{ride_id}/messages` : write to shard
  - [ ] `GET /api/v1/rides/{ride_id}/messages` : read from shard
  
- [ ] Review endpoints
  - [ ] `POST /api/v1/rides/{ride_id}/reviews` : write to shard
  - [ ] `GET /api/v1/rides/{ride_id}/reviews` : read from shard
  
- [ ] Settlement endpoints
  - [ ] Rides-related settlement operations : route via RideID

Multi-Shard Operations:
- [x] `GET /api/v1/rides` (list all) : fan-out to 3 shards, merge by RideID
- [x] Admin ride listings + stats : fan-out/aggregate across shards
- [ ] Range queries : cross-shard aggregation

> Extract and generalize multi-shard fan-out + merge logic into reusable utilities.

Utilities to Create:
- [x] `list_rides_across_shards(filter, sort)` : queries all 3 shards, merges results
- [ ] `list_bookings_by_ride_range(start_ride_id, end_ride_id)` : cross-shard aggregation
- [ ] Generic merge/dedup helper for common operations
- [x] Integrate into main endpoints (e.g., `GET /rides` route)

> Execute complete workflow with validation.

- [ ] Generate fake data: `uv run python -m scripts.generate_fake_data --rides 120 --members 80 --reset-ride-data`
- [ ] Run migration: `uv run python -m scripts.migrate_rides_to_shards`
- [ ] Validate migration: `uv run python -m scripts.validate_shard_migration`
- [ ] Test endpoint routing via demo APIs
- [x] Test Phase 2 endpoints (single-shard operations)
- [x] Test Phase 3 endpoints (cross-shard operations)
- [ ] Verify data isolation (confirm rides in shard_0 stay in shard_0)
- [ ] Performance baseline: Monitor query latency before/after sharding

- [x] Add automated tests for shard utilities + ride/admin shard routes

- [ ] Create orchestration script (run all steps with one command)
- [ ] Load test across shards (concurrent operations)

---

Sharded Tables: Rides, Bookings, Ride_Chat, Ride_Participants, Reputation_Reviews, Cost_Settlements

Replicated Tables (per shard): Members, Auth_Credentials

Global Tables (primary DB only): Locations, Saved_Addresses, User_Preferences, Ride_Shard_Directory
