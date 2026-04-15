from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_current_admin_credential
from core.sharding import get_ride_shard_id
from db.session import get_db_session
from db.sharding import SHARD_SESSION_MAKERS, shard_id_for_ride_id
from models.auth_credential import AuthCredential

router = APIRouter(prefix="/testing/sharding", tags=["testing", "sharding"])

RIDE_CENTRIC_TABLES = [
    "Rides",
    "Bookings",
    "Ride_Chat",
    "Ride_Participants",
    "Reputation_Reviews",
    "Cost_Settlements",
]


def _shard_ride_lookup(shard_id: int, ride_id: int) -> dict[str, object] | None:
    shard_db = SHARD_SESSION_MAKERS[shard_id]()
    try:
        row = shard_db.execute(
            text(
                """
                SELECT RideID, Host_MemberID, Start_GeoHash, End_GeoHash, Departure_Time, Ride_Status
                FROM Rides
                WHERE RideID = :ride_id
                """
            ),
            {"ride_id": ride_id},
        ).mappings().first()
        return dict(row) if row else None
    finally:
        shard_db.close()


def _candidate_shards_for_range(start_ride_id: int, end_ride_id: int) -> list[int]:
    if end_ride_id - start_ride_id + 1 >= 3:
        return [0, 1, 2]

    shards = set()
    for ride_id in range(start_ride_id, end_ride_id + 1):
        shards.add(shard_id_for_ride_id(ride_id))
    return sorted(shards)


@router.get("/ride/{ride_id}")
def ride_shard_lookup(
    ride_id: int,
    _: AuthCredential = Depends(get_current_admin_credential),
    db: Session = Depends(get_db_session),
) -> dict[str, object]:
    shard_id = get_ride_shard_id(ride_id, db)
    deterministic_shard = shard_id_for_ride_id(ride_id)
    ride = _shard_ride_lookup(shard_id, ride_id)

    return {
        "ride_id": ride_id,
        "resolved_shard_id": shard_id,
        "deterministic_shard_id": deterministic_shard,
        "route_consistent": shard_id == deterministic_shard,
        "ride_found_on_resolved_shard": ride is not None,
        "ride": ride,
    }


@router.get("/rides/range")
def range_query_across_shards(
    start_ride_id: int = Query(..., ge=1),
    end_ride_id: int = Query(..., ge=1),
    limit: int = Query(default=100, ge=1, le=500),
    _: AuthCredential = Depends(get_current_admin_credential),
) -> dict[str, object]:
    if start_ride_id > end_ride_id:
        start_ride_id, end_ride_id = end_ride_id, start_ride_id

    shard_ids = _candidate_shards_for_range(start_ride_id, end_ride_id)
    per_shard_counts: dict[int, int] = {}
    merged_rows: list[dict[str, object]] = []

    for shard_id in shard_ids:
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            rows = shard_db.execute(
                text(
                    """
                    SELECT RideID, Host_MemberID, Start_GeoHash, End_GeoHash, Departure_Time, Ride_Status
                    FROM Rides
                    WHERE RideID BETWEEN :start_ride_id AND :end_ride_id
                    ORDER BY RideID ASC
                    LIMIT :limit
                    """
                ),
                {
                    "start_ride_id": start_ride_id,
                    "end_ride_id": end_ride_id,
                    "limit": limit,
                },
            ).mappings().all()
            dict_rows = [dict(row) for row in rows]
            per_shard_counts[shard_id] = len(dict_rows)
            merged_rows.extend(dict_rows)
        finally:
            shard_db.close()

    merged_rows.sort(key=lambda row: int(row["RideID"]))
    merged_rows = merged_rows[:limit]

    return {
        "start_ride_id": start_ride_id,
        "end_ride_id": end_ride_id,
        "candidate_shards": shard_ids,
        "per_shard_counts": per_shard_counts,
        "returned_count": len(merged_rows),
        "rows": merged_rows,
    }


@router.get("/distribution")
def shard_distribution(
    _: AuthCredential = Depends(get_current_admin_credential),
    db: Session = Depends(get_db_session),
) -> dict[str, object]:
    directory_counts = {
        int(row[0]): int(row[1])
        for row in db.execute(
            text(
                """
                SELECT ShardID, COUNT(*)
                FROM Ride_Shard_Directory
                GROUP BY ShardID
                ORDER BY ShardID
                """
            )
        ).all()
    }

    shard_table_counts: dict[int, dict[str, int]] = {0: {}, 1: {}, 2: {}}
    for shard_id in (0, 1, 2):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            for table in RIDE_CENTRIC_TABLES:
                count = shard_db.scalar(text(f"SELECT COUNT(*) FROM `{table}`")) or 0
                shard_table_counts[shard_id][table] = int(count)
        finally:
            shard_db.close()

    return {
        "directory_counts": directory_counts,
        "shard_table_counts": shard_table_counts,
    }
