from __future__ import annotations

from api.routes import rides as rides_route


def test_list_rides_only_open_uses_open_filter(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_list_rides_across_shards(*, statuses, limit, order_desc):
        captured["statuses"] = statuses
        captured["limit"] = limit
        captured["order_desc"] = order_desc
        return ["ok"]

    monkeypatch.setattr(rides_route, "list_rides_across_shards", _fake_list_rides_across_shards)

    result = rides_route.list_rides(only_open=True, limit=12)

    assert result == ["ok"]
    assert captured == {
        "statuses": ("Open",),
        "limit": 12,
        "order_desc": False,
    }


def test_list_rides_open_and_full_filter(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_list_rides_across_shards(*, statuses, limit, order_desc):
        captured["statuses"] = statuses
        captured["limit"] = limit
        captured["order_desc"] = order_desc
        return ["ok"]

    monkeypatch.setattr(rides_route, "list_rides_across_shards", _fake_list_rides_across_shards)

    result = rides_route.list_rides(only_open=False, limit=30)

    assert result == ["ok"]
    assert captured == {
        "statuses": ("Open", "Full"),
        "limit": 30,
        "order_desc": False,
    }
