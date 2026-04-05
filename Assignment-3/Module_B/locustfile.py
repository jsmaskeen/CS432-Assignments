from __future__ import annotations

import os
import random
import string
from collections import deque
from datetime import UTC, datetime, timedelta
from typing import Any

from gevent.lock import Semaphore
from locust import HttpUser, between, events, tag, task
from locust.exception import StopUser

API_PREFIX = os.getenv("LOCUST_API_PREFIX", "/api/v1")
PASSWORD = os.getenv("LOCUST_DEFAULT_PASSWORD", "password123!")
ADMIN_BOOTSTRAP_USERNAME = os.getenv("ADMIN_BOOTSTRAP_USERNAME", "admin")
RACE_HOST_USERNAME = os.getenv("LOCUST_RACE_HOST_USERNAME", "locust_race_host")
RACE_RIDE_CAPACITY = int(os.getenv("LOCUST_RACE_RIDE_CAPACITY", "2"))
CONTENTION_MODE = os.getenv("LOCUST_CONTENTION_MODE", "signal").lower()
FAILURE_ACCEPT_HOOK = os.getenv("LOCUST_FAILURE_ACCEPT_HOOK", "bookings.accept.post_flush")
FAILURE_END_HOOK = os.getenv("LOCUST_FAILURE_END_HOOK", "rides.end.before_settlement_insert")

GEOHASH_CHARS = "0123456789bcdefghjkmnpqrstuvwxyz"


def random_suffix(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def random_phone() -> str:
    return "".join(random.choices(string.digits, k=10))


def random_geohash(prefix: str = "ts5") -> str:
    # ts7 is the geohash prefix for ahmedabad area.
    body = "".join(random.choices(GEOHASH_CHARS, k=7))
    return f"{prefix}{body}" if prefix else body


def ride_payload(max_capacity: int = 4) -> dict[str, Any]:
    start_geohash = random_geohash()
    end_geohash = random_geohash()
    while end_geohash == start_geohash:
        end_geohash = random_geohash()

    return {
        "start_geohash": start_geohash,
        "end_geohash": end_geohash,
        "departure_time": (datetime.now(UTC) + timedelta(days=2, hours=random.randint(1, 12))).isoformat(),
        "vehicle_type": "Sedan",
        "max_capacity": max_capacity,
        "base_fare_per_km": "15.00",
    }


def booking_payload() -> dict[str, str]:
    pickup = random_geohash()
    drop = random_geohash()
    while drop == pickup:
        drop = random_geohash()
    return {
        "pickup_geohash": pickup,
        "drop_geohash": drop,
    }


class SharedState:
    def __init__(self) -> None:
        self.lock = Semaphore()
        self.bootstrap_lock = Semaphore()
        self.open_rides: deque[int] = deque(maxlen=300)
        self.race_ride_id: int | None = None
        self.race_host_member_id: int | None = None
        self.race_generation: int = 0
        self.account_seq: dict[str, int] = {"host": 0, "rider": 0}

    def reset(self) -> None:
        with self.lock:
            self.open_rides.clear()
            self.race_ride_id = None
            self.race_host_member_id = None
            self.race_generation = 0
            self.account_seq = {"host": 0, "rider": 0}

    def push_open_ride(self, ride_id: int) -> None:
        with self.lock:
            self.open_rides.append(ride_id)

    def sample_open_ride(self) -> int | None:
        with self.lock:
            if not self.open_rides:
                return None
            return random.choice(list(self.open_rides))


shared_state = SharedState()


@events.test_start.add_listener
def on_test_start(environment, **_kwargs):
    shared_state.reset()


class RajakUserBase(HttpUser):
    abstract = True
    wait_time = between(1, 3)

    token: str | None = None
    username: str = ""

    @staticmethod
    def _safe_json(response) -> dict[str, Any]:
        try:
            return response.json()
        except Exception:
            return {}

    def api_path(self, path: str) -> str:
        return f"{API_PREFIX}{path}"

    def auth_headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    @staticmethod
    def _handle_contention_response(
        response,
        *,
        success_statuses: set[int],
        contention_statuses: set[int],
        operation_label: str,
    ) -> None:
        if response.status_code in success_statuses:
            response.success()
            return

        if response.status_code in contention_statuses:
            if CONTENTION_MODE == "ignore":
                response.success()
            else:
                # If details are provided in the response, it can help in debugging contention issues.
                details = response.json().get("detail") if response.content else "No details"
                response.failure(f"race-contention {operation_label} status={response.status_code} details: {details}")
            return

        response.failure(f"unexpected status {response.status_code}")

    def _register(self, username: str, password: str) -> tuple[int, dict[str, Any]]:
        payload = {
            "username": username,
            "password": password,
            "email": f"{username}@iitgn.ac.in",
            "full_name": f"Locust {username}",
            "phone_number": random_phone(),
            "gender": random.choice(["Male", "Female", "Other"]),
        }
        with self.client.post(
            self.api_path("/auth/register"),
            json=payload,
            name="BOOTSTRAP POST /auth/register",
            catch_response=True,
        ) as res:
            body = self._safe_json(res)
            if res.status_code in {201, 409}:
                res.success()
            else:
                res.failure(f"bootstrap register unexpected status {res.status_code}")
            return res.status_code, body

    def _login(self, username: str, password: str) -> tuple[int, dict[str, Any]]:
        with self.client.post(
            self.api_path("/auth/login"),
            json={"username": username, "password": password},
            name="BOOTSTRAP POST /auth/login",
            catch_response=True,
        ) as res:
            body = self._safe_json(res)
            if res.status_code == 200:
                res.success()
            else:
                res.failure(f"bootstrap login unexpected status {res.status_code}")
            return res.status_code, body

    def login_or_register(self, username: str, password: str = PASSWORD) -> None:
        token: str | None = None
        register_status, register_body = self._register(username, password)
        if register_status == 201:
            token = register_body.get("access_token")

        if token is None:
            login_status, login_body = self._login(username, password)
            if login_status == 200:
                token = login_body.get("access_token")

        if not token:
            raise StopUser("Unable to bootstrap auth token")

        self.token = token
        self.username = username

    def register_fresh_account(self, prefix: str, password: str = PASSWORD, attempts: int = 5) -> None:
        for _ in range(attempts):
            with shared_state.bootstrap_lock:
                seq = shared_state.account_seq.get(prefix, 0) + 1
                shared_state.account_seq[prefix] = seq
                username = f"{prefix}_vu_{seq:04d}"

                status_code, body = self._register(username, password)
                token: str | None = None

                if status_code == 201:
                    token = body.get("access_token")
                elif status_code == 409:
                    login_status, login_body = self._login(username, password)
                    if login_status == 200:
                        token = login_body.get("access_token")

            if token:
                self.token = token
                self.username = username
                return
        raise StopUser(f"Unable to create fresh account for prefix={prefix}")

    def create_ride(self, capacity: int = 4, endpoint_name: str = "POST /rides") -> int | None:
        res = self.client.post(
            self.api_path("/rides"),
            headers=self.auth_headers(),
            json=ride_payload(max_capacity=capacity),
            name=endpoint_name,
        )
        if res.status_code == 201:
            ride_id = res.json().get("RideID")
            if isinstance(ride_id, int):
                shared_state.push_open_ride(ride_id)
                return ride_id
        return None


class HostConcurrentUser(RajakUserBase):
    weight = 4

    def on_start(self) -> None:
        self.register_fresh_account("host")
        self.owned_rides: deque[int] = deque()

    @tag("concurrent", "stress")
    @task(4)
    def create_open_ride(self) -> None:
        ride_id = self.create_ride(capacity=random.randint(3, 5))
        if ride_id:
            self.owned_rides.append(ride_id)

    @tag("concurrent", "stress")
    @task(5)
    def manage_pending_bookings(self) -> None:
        ride_id = random.choice(list(self.owned_rides)) if self.owned_rides else None
        if not ride_id:
            return
        
        open_res = self.client.get(
            self.api_path(f"/rides/{ride_id}"),
            headers=self.auth_headers(),
            name="GET /rides/{ride_id}",
        )
        if open_res.status_code != 200:
            return
        if open_res.json().get("Ride_Status") != "Open":
            return
        pending_res = self.client.get(
            self.api_path(f"/rides/{ride_id}/bookings/pending"),
            headers=self.auth_headers(),
            name="GET /rides/{ride_id}/bookings/pending",
        )
        if pending_res.status_code != 200:
            return

        pending = pending_res.json()
        if not pending:
            return

        booking_id = random.choice(pending).get("BookingID")
        if not booking_id:
            return

        if random.random() < 0.7:
            with self.client.post(
                self.api_path(f"/rides/bookings/{booking_id}/accept"),
                headers=self.auth_headers(),
                name="POST /rides/bookings/{booking_id}/accept",
                catch_response=True,
            ) as res:
                self._handle_contention_response(
                    res,
                    success_statuses={200},
                    contention_statuses={400, 404, 409},
                    operation_label="accept",
                )
        else:
            self.client.post(
                self.api_path(f"/rides/bookings/{booking_id}/reject"),
                headers=self.auth_headers(),
                name="POST /rides/bookings/{booking_id}/reject",
            )

    @tag("concurrent", "stress")
    @task(2)
    def start_or_end_ride(self) -> None:
        ride_id = random.choice(list(self.owned_rides)) if self.owned_rides else None
        if not ride_id:
            return

        get_res = self.client.get(
            self.api_path(f"/rides/{ride_id}"),
            headers=self.auth_headers(),
            name="GET /rides/{ride_id}",
        )
        if get_res.status_code != 200:
            return

        status = get_res.json().get("Ride_Status")
        if status in {"Open", "Full"} and random.random() < 0.5:
            start_res = self.client.post(
                self.api_path(f"/rides/{ride_id}/start"),
                headers=self.auth_headers(),
                name="POST /rides/{ride_id}/start",
            )
        elif status == "Started":
            end_res = self.client.post(
                self.api_path(f"/rides/{ride_id}/end"),
                headers=self.auth_headers(),
                name="POST /rides/{ride_id}/end",
            )
            
    @tag("concurrent", "stress")
    @task(3)
    def browse_rides(self) -> None:
        self.client.get(
            self.api_path("/rides"),
            params={"only_open": random.choice(["true", "false"]), "limit": random.randint(10, 50)},
            name="GET /rides",
        )

    @tag("race", "racing", "failure")
    @task(1)
    def race_idle(self) -> None:
        self.client.get(
            self.api_path("/health"),
            name="GET /health",
        )


class RiderConcurrentUser(RajakUserBase):
    weight = 7
    booked_rides: deque[int] = deque()

    def on_start(self) -> None:
        self.register_fresh_account("rider")
        self.last_race_generation_attempted: int = -1

    @tag("concurrent", "stress")
    @task(7)
    def browse_open_rides(self) -> None:
        self.client.get(
            self.api_path("/rides"),
            params={"only_open": "true", "limit": random.randint(20, 60)},
            name="GET /rides",
        )

    @tag("concurrent", "stress")
    @task(5)
    def book_open_ride(self) -> None:
        list_res = self.client.get(
            self.api_path("/rides"),
            params={"only_open": "true", "limit": 40},
            name="GET /rides",
        )
        if list_res.status_code != 200:
            return

        rides = list_res.json()
        if not rides:
            return
        ride = random.choice(rides)
        ride_id = ride.get("RideID")
        if not ride_id:
            return
        if ride_id in self.booked_rides:
            return
        with self.client.post(
            self.api_path(f"/rides/{ride_id}/book"),
            headers=self.auth_headers(),
            json=booking_payload(),
            name="POST /rides/{ride_id}/book",
            catch_response=True,
        ) as res:
            self._handle_contention_response(
                res,
                success_statuses={201},
                contention_statuses={400, 404, 409},
                operation_label="book",
            )
            if res.status_code == 201:
                self.booked_rides.append(ride_id)

    @tag("concurrent", "stress")
    @task(3)
    def my_bookings(self) -> None:
        self.client.get(
            self.api_path("/rides/my/bookings"),
            headers=self.auth_headers(),
            name="GET /rides/my/bookings",
        )

    @tag("race", "racing", "failure")
    @task(4)
    def race_book_shared_ride(self) -> None:
        with shared_state.lock:
            race_ride_id = shared_state.race_ride_id
            generation = shared_state.race_generation

        if not race_ride_id or generation == self.last_race_generation_attempted:
            return

        with self.client.post(
            self.api_path(f"/rides/{race_ride_id}/book"),
            headers=self.auth_headers(),
            json=booking_payload(),
            name="RACE POST /rides/{ride_id}/book",
            catch_response=True,
        ) as res:
            self._handle_contention_response(
                res,
                success_statuses={201},
                contention_statuses={400, 404, 409},
                operation_label="race-book",
            )

        self.last_race_generation_attempted = generation


class AdminObserverUser(RajakUserBase):
    fixed_count = 1
    weight = 0

    def on_start(self) -> None:
        self.login_or_register(ADMIN_BOOTSTRAP_USERNAME)

    @tag("concurrent", "race", "racing", "stress", "failure")
    @task(3)
    def ride_stats(self) -> None:
        with self.client.get(
            self.api_path("/admin/rides/stats"),
            headers=self.auth_headers(),
            name="GET /admin/rides/stats",
            catch_response=True,
        ) as res:
            if res.status_code == 200:
                res.success()
            elif res.status_code == 403:
                res.failure(
                    "admin access denied; set ADMIN_BOOTSTRAP_USERNAME to an admin account before running locust"
                )
            else:
                res.failure(f"unexpected status {res.status_code}")

    @tag("concurrent", "race", "racing", "stress", "failure")
    @task(2)
    def open_rides(self) -> None:
        self.client.get(
            self.api_path("/admin/rides/open"),
            headers=self.auth_headers(),
            name="GET /admin/rides/open",
        )


class RaceHostUser(RajakUserBase):
    fixed_count = 1
    weight = 0

    def on_start(self) -> None:
        self.login_or_register(RACE_HOST_USERNAME)
        active_tags = set(getattr(self.environment.parsed_options, "tags", []) or [])
        if "race" in active_tags or "failure" in active_tags:
            self.ensure_race_ride()

    def ensure_race_ride(self) -> None:
        with shared_state.lock:
            race_ride_id = shared_state.race_ride_id

        if race_ride_id:
            return

        ride_id = self.create_ride(capacity=RACE_RIDE_CAPACITY, endpoint_name="RACE POST /rides")
        if not ride_id:
            return

        with shared_state.lock:
            shared_state.race_ride_id = ride_id
            shared_state.race_host_member_id = -1
            shared_state.race_generation += 1

    @tag("race", "racing", "failure")
    @task(5)
    def race_accept_or_reject(self) -> None:
        self.ensure_race_ride()
        with shared_state.lock:
            ride_id = shared_state.race_ride_id

        if not ride_id:
            return
        
        ride_res = self.client.get(
            self.api_path(f"/rides/{ride_id}"),
            headers=self.auth_headers(),
            name="RACE GET /rides/{ride_id}",
        )
        if ride_res.status_code != 200:
            return
        if ride_res.json().get("Ride_Status") != "Open":
            return

        pending_res = self.client.get(
            self.api_path(f"/rides/{ride_id}/bookings/pending"),
            headers=self.auth_headers(),
            name="RACE GET /rides/{ride_id}/bookings/pending",
        )
        if pending_res.status_code != 200:
            return

        pending = pending_res.json()
        if not pending:
            return

        booking_id = random.choice(pending).get("BookingID")
        if not booking_id:
            return

        endpoint = "accept" if random.random() < 0.75 else "reject"
        with self.client.post(
            self.api_path(f"/rides/bookings/{booking_id}/{endpoint}"),
            headers=self.auth_headers(),
            name=f"RACE POST /rides/bookings/{{booking_id}}/{endpoint}",
            catch_response=True,
        ) as res:
            self._handle_contention_response(
                res,
                success_statuses={200},
                contention_statuses={400, 404, 409},
                operation_label=f"race-{endpoint}",
            )

    @tag("race", "racing", "failure")
    @task(2)
    def rollover_race_ride_if_closed(self) -> None:
        with shared_state.lock:
            ride_id = shared_state.race_ride_id

        if not ride_id:
            self.ensure_race_ride()
            return

        get_res = self.client.get(
            self.api_path(f"/rides/{ride_id}"),
            headers=self.auth_headers(),
            name="RACE GET /rides/{ride_id}",
        )
        if get_res.status_code != 200:
            with shared_state.lock:
                shared_state.race_ride_id = None
            self.ensure_race_ride()
            return

        status = get_res.json().get("Ride_Status")
        seats = get_res.json().get("Available_Seats", 0)
        if status != "Open" or seats == 0:
            new_ride_id = self.create_ride(capacity=RACE_RIDE_CAPACITY, endpoint_name="RACE POST /rides")
            if not new_ride_id:
                return
            with shared_state.lock:
                shared_state.race_ride_id = new_ride_id
                shared_state.race_host_member_id = -1
                shared_state.race_generation += 1

    @tag("concurrent", "stress")
    @task(1)
    def concurrent_health_ping(self) -> None:
        self.client.get(
            self.api_path("/rides"),
            params={"only_open": "true", "limit": 10},
            name="GET /rides",
        )


class ChaosAdminUser(RajakUserBase):
    fixed_count = 1
    weight = 0

    def on_start(self) -> None:
        active_tags = set(getattr(self.environment.parsed_options, "tags", []) or [])
        if "failure" not in active_tags:
            raise StopUser()
        self.login_or_register(ADMIN_BOOTSTRAP_USERNAME)
        self.client.post(
            self.api_path("/testing/chaos/reset"),
            headers=self.auth_headers(),
            name="FAILURE POST /testing/chaos/reset",
        )

    @tag("failure")
    @task(5)
    def inject_accept_failures(self) -> None:
        self.client.post(
            self.api_path("/testing/chaos/enable"),
            headers=self.auth_headers(),
            json={"hook": FAILURE_ACCEPT_HOOK, "fail_count": 1},
            name="FAILURE POST /testing/chaos/enable accept",
        )

    @tag("failure")
    @task(1)
    def inject_end_ride_failures(self) -> None:
        self.client.post(
            self.api_path("/testing/chaos/enable"),
            headers=self.auth_headers(),
            json={"hook": FAILURE_END_HOOK, "fail_count": 1},
            name="FAILURE POST /testing/chaos/enable end",
        )


