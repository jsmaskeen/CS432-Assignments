from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from api.routes import admin as admin_route


class _FakeScalarDB:
    def __init__(self, scalar_value: int) -> None:
        self._scalar_value = scalar_value

    def scalar(self, _stmt):
        return self._scalar_value


def test_ride_stats_uses_cross_shard_aggregates(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_route,
        "aggregate_ride_booking_stats_across_shards",
        lambda: {
            "total_rides": 15,
            "open_rides": 4,
            "full_rides": 3,
            "cancelled_rides": 2,
            "completed_rides": 5,
            "total_bookings": 22,
            "pending_bookings": 6,
            "confirmed_bookings": 10,
            "rejected_bookings": 3,
            "cancelled_bookings": 3,
            "total_capacity_seats": 90,
            "total_available_seats": 21,
            "average_base_fare_per_km": 18.5,
        },
    )

    response = admin_route.ride_stats(_=None, db=_FakeScalarDB(12))

    assert response.total_members == 12
    assert response.total_rides == 15
    assert response.open_rides == 4
    assert response.full_rides == 3
    assert response.cancelled_rides == 2
    assert response.completed_rides == 5
    assert response.total_bookings == 22
    assert response.pending_bookings == 6
    assert response.confirmed_bookings == 10
    assert response.rejected_bookings == 3
    assert response.cancelled_bookings == 3
    assert response.total_capacity_seats == 90
    assert response.total_available_seats == 21
    assert response.total_booked_seats == 69
    assert response.average_base_fare_per_km == 18.5


@pytest.mark.parametrize(
    ("route_name", "expected_statuses", "expected_order_desc"),
    [
        ("list_active_rides", ("Started",), False),
        ("list_open_rides", ("Open",), False),
        ("list_completed_rides", ("Completed",), True),
    ],
)
def test_admin_ride_lists_delegate_to_cross_shard_query(
    monkeypatch,
    route_name: str,
    expected_statuses: tuple[str, ...],
    expected_order_desc: bool,
) -> None:
    captured: dict[str, object] = {}

    ride = SimpleNamespace(
        RideID=99,
        Host_MemberID=7,
        Start_GeoHash="u09tun",
        End_GeoHash="u09tvw",
        Departure_Time=datetime(2026, 1, 1, 12, 0, 0),
        Vehicle_Type="Sedan",
        Max_Capacity=4,
        Available_Seats=2,
        Base_Fare_Per_KM=Decimal("13.50"),
        Ride_Status=expected_statuses[0],
        Created_At=datetime(2026, 1, 1, 10, 0, 0),
    )

    def _fake_list_rides_across_shards(*, statuses, order_desc, limit=None):
        captured["statuses"] = statuses
        captured["order_desc"] = order_desc
        captured["limit"] = limit
        return [ride]

    monkeypatch.setattr(admin_route, "list_rides_across_shards", _fake_list_rides_across_shards)

    route_fn = getattr(admin_route, route_name)
    result = route_fn(_=None)

    assert captured == {
        "statuses": expected_statuses,
        "order_desc": expected_order_desc,
        "limit": None,
    }
    assert len(result) == 1
    assert result[0].ride_id == 99
    assert result[0].host_member_id == 7
    assert result[0].ride_status == expected_statuses[0]
