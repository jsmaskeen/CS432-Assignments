import json
import os
import random
import string
import time
from datetime import datetime, timedelta
from importlib import util as importlib_util
from pathlib import Path

import requests


if importlib_util.find_spec("tqdm") is not None:
    _tqdm_module = __import__("tqdm")

    def tqdm(iterable, **kwargs):
        return _tqdm_module.tqdm(iterable, **kwargs)
else:
    def tqdm(iterable, **_kwargs):
        return iterable

BASE_URL = "http://127.0.0.1:8000/api/v1"
SLIM_SPEC_PATH = Path(__file__).with_name("slim_openapi_subsections.json")
RESULTS_PATH = Path(__file__).with_name("profiling_results.json")
MARKDOWN_RESULTS_PATH = Path(__file__).with_name("profiling_results.md")

READ_ITERATIONS = 20
WRITE_ITERATIONS = 20
STATEFUL_ITERATIONS = 20
REQUEST_TIMEOUT = 20
GEOHASH_CHARS = "0123456789bcdefghjkmnpqrstuvwxyz"

results: dict[str, dict] = {}
state: dict[str, object] = {
    "admin": {"token": "", "member_id": None, "username": None},
    "host": {"token": "", "member_id": None, "username": None},
    "rider": {"token": "", "member_id": None, "username": None},
    "open_ride_id": None,
    "lifecycle_ride_id": None,
    "started_ride_id": None,
    "completed_ride_id": None,
    "delete_ride_id": None,
    "booking_accept_id": None,
    "booking_reject_id": None,
    "booking_delete_id": None,
    "booking_settlement_id": None,
    "settlement_id": None,
    "saved_address_id": None,
    "location_id": None,
    "review_id": None,
    "admin_table_name": "Locations",
    "admin_inserted_pk": -1,
    "login_users": [],
}


def random_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def random_phone() -> str:
    return "".join(random.choices(string.digits, k=10))


def random_geohash(prefix: str = "gh") -> str:
    return f"{prefix}{''.join(random.choices(GEOHASH_CHARS, k=6))}"


def auth_header(token: str | None) -> dict[str, str] | None:
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def register_or_login(username: str, password: str, full_name: str, gender: str) -> tuple[str, int | None]:
    register_payload = {
        "username": username,
        "password": password,
        "email": f"{username}@iitgn.ac.in",
        "full_name": full_name,
        "phone_number": random_phone(),
        "gender": gender,
    }
    requests.post(f"{BASE_URL}/auth/register", json=register_payload, timeout=REQUEST_TIMEOUT)

    login_res = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password},
        timeout=REQUEST_TIMEOUT,
    )
    token = login_res.json().get("access_token", "") if login_res.status_code < 400 else ""

    member_id = None
    if token:
        me_res = requests.get(f"{BASE_URL}/auth/me", headers=auth_header(token), timeout=REQUEST_TIMEOUT)
        if me_res.status_code == 200:
            member_id = me_res.json().get("member_id")

    return token, member_id


def bootstrap_state() -> None:
    print("--- Bootstrapping profiling state ---")
    password = "password123!"

    admin_candidates = [
        os.getenv("ADMIN_BOOTSTRAP_USERNAME", ""),
        "admin_user_001",
        "admin",
    ]
    admin_candidates = [candidate for candidate in admin_candidates if candidate]

    admin_token = ""
    admin_member_id = None
    admin_username = None
    for candidate in admin_candidates:
        token, member_id = register_or_login(candidate, password, "Admin User", "Female")
        if not token:
            continue
        me_res = requests.get(f"{BASE_URL}/auth/me", headers=auth_header(token), timeout=REQUEST_TIMEOUT)
        if me_res.status_code == 200 and me_res.json().get("role") == "admin":
            admin_token = token
            admin_member_id = member_id
            admin_username = candidate
            break

    host_username = f"host_{random_string(6)}"
    rider_username = f"rider_{random_string(6)}"
    host_token, host_member_id = register_or_login(host_username, password, "Host User", "Male")
    rider_token, rider_member_id = register_or_login(rider_username, password, "Rider User", "Female")

    state["admin"] = {"token": admin_token, "member_id": admin_member_id, "username": admin_username}
    state["host"] = {"token": host_token, "member_id": host_member_id, "username": host_username}
    state["rider"] = {"token": rider_token, "member_id": rider_member_id, "username": rider_username}

    if not host_token or not rider_token:
        raise RuntimeError("Failed to create host/rider users. Check backend auth service.")

    location_payload = {
        "location_name": f"Profiling Spot {random_string(4)}",
        "location_type": "Pickup",
        "geohash": f"gh{random_string(6)}",
    }
    loc_res = requests.post(f"{BASE_URL}/locations", json=location_payload, timeout=REQUEST_TIMEOUT)
    if loc_res.status_code == 201:
        state["location_id"] = loc_res.json().get("LocationID")

    open_ride = create_ride(host_token)
    lifecycle_ride = create_ride(host_token)
    started_ride = create_ride(host_token)
    completed_ride = create_ride(host_token)
    accept_ride = create_ride(host_token)
    reject_ride = create_ride(host_token)
    delete_booking_ride = create_ride(host_token)

    state["open_ride_id"] = open_ride
    state["lifecycle_ride_id"] = lifecycle_ride
    state["started_ride_id"] = started_ride
    state["completed_ride_id"] = completed_ride

    if started_ride:
        requests.post(f"{BASE_URL}/rides/{started_ride}/start", headers=auth_header(host_token), timeout=REQUEST_TIMEOUT)

    if completed_ride:
        booking_for_settlement = create_booking(completed_ride, rider_token)
        if booking_for_settlement:
            requests.post(
                f"{BASE_URL}/rides/bookings/{booking_for_settlement}/accept",
                headers=auth_header(host_token),
                timeout=REQUEST_TIMEOUT,
            )
            requests.post(f"{BASE_URL}/rides/{completed_ride}/start", headers=auth_header(host_token), timeout=REQUEST_TIMEOUT)
            requests.post(f"{BASE_URL}/rides/{completed_ride}/end", headers=auth_header(host_token), timeout=REQUEST_TIMEOUT)
            state["booking_settlement_id"] = booking_for_settlement
            set_res = requests.get(
                f"{BASE_URL}/settlements/booking/{booking_for_settlement}",
                headers=auth_header(rider_token),
                timeout=REQUEST_TIMEOUT,
            )
            if set_res.status_code == 200 and set_res.json():
                state["settlement_id"] = set_res.json().get("SettlementID")

    if accept_ride:
        accept_booking = create_booking(accept_ride, rider_token)
    else:
        accept_booking = None

    if reject_ride:
        reject_booking = create_booking(reject_ride, rider_token)
    else:
        reject_booking = None

    if delete_booking_ride:
        delete_booking = create_booking(delete_booking_ride, rider_token)
    else:
        delete_booking = None

    state["booking_accept_id"] = accept_booking
    state["booking_reject_id"] = reject_booking
    state["booking_delete_id"] = delete_booking

    if state.get("location_id"):
        saved_res = requests.post(
            f"{BASE_URL}/saved-addresses",
            headers=auth_header(host_token),
            json={"label": f"Home {random_string(3)}", "location_id": state["location_id"]},
            timeout=REQUEST_TIMEOUT,
        )
        if saved_res.status_code == 201:
            state["saved_address_id"] = saved_res.json().get("AddressID")

    if completed_ride and host_member_id and rider_token:
        review_res = requests.post(
            f"{BASE_URL}/reviews",
            headers=auth_header(rider_token),
            json={
                "ride_id": completed_ride,
                "reviewee_member_id": host_member_id,
                "rating": 5,
                "comments": "Great ride",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if review_res.status_code == 201:
            state["review_id"] = review_res.json().get("ReviewID")

    if admin_token:
        delete_ride = create_ride(admin_token)
        state["delete_ride_id"] = delete_ride

    login_users: list[dict[str, str]] = []
    for _ in range(max(WRITE_ITERATIONS, 10)):
        login_username = f"login_{random_string(8)}"
        login_password = "password123!"
        payload = {
            "username": login_username,
            "password": login_password,
            "email": f"{login_username}@iitgn.ac.in",
            "full_name": "Login Profile User",
            "phone_number": random_phone(),
            "gender": random.choice(["Male", "Female", "Other"]),
        }
        requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=REQUEST_TIMEOUT)
        login_users.append({"username": login_username, "password": login_password})
    state["login_users"] = login_users


def create_ride(token: str) -> int | None:
    start_geohash = random_geohash("st")
    end_geohash = random_geohash("en")
    while end_geohash == start_geohash:
        end_geohash = random_geohash("en")

    payload = {
        "start_geohash": start_geohash,
        "end_geohash": end_geohash,
        "departure_time": (datetime.now() + timedelta(days=3, hours=random.randint(1, 12))).isoformat(),
        "vehicle_type": "Sedan",
        "max_capacity": 4,
        "base_fare_per_km": "15.00",
    }
    res = requests.post(f"{BASE_URL}/rides", headers=auth_header(token), json=payload, timeout=REQUEST_TIMEOUT)
    return res.json().get("RideID") if res.status_code == 201 else None


def create_booking(ride_id: int, token: str) -> int | None:
    payload = {
        "pickup_geohash": "a1b2c3",
        "drop_geohash": "d4e5f6",
    }
    res = requests.post(f"{BASE_URL}/rides/{ride_id}/book", headers=auth_header(token), json=payload, timeout=REQUEST_TIMEOUT)
    return res.json().get("BookingID") if res.status_code == 201 else None


def create_location() -> int | None:
    payload = {
        "location_name": f"Loc {random_string(7)}",
        "location_type": random.choice(["Pickup", "Drop", "Transit"]),
        "geohash": random_geohash(),
    }
    res = requests.post(f"{BASE_URL}/locations", json=payload, timeout=REQUEST_TIMEOUT)
    return res.json().get("LocationID") if res.status_code == 201 else None


def create_started_ride(token: str) -> int | None:
    ride_id = create_ride(token)
    if not ride_id:
        return None
    requests.post(f"{BASE_URL}/rides/{ride_id}/start", headers=auth_header(token), timeout=REQUEST_TIMEOUT)
    return ride_id


def create_pending_booking_pair(host_token: str, rider_token: str) -> tuple[int | None, int | None]:
    ride_id = create_ride(host_token)
    if not ride_id:
        return None, None
    booking_id = create_booking(ride_id, rider_token)
    return ride_id, booking_id


def create_completed_ride_context(host_token: str, rider_token: str) -> tuple[int | None, int | None, int | None]:
    ride_id, booking_id = create_pending_booking_pair(host_token, rider_token)
    if not ride_id or not booking_id:
        return None, None, None

    accept_res = requests.post(
        f"{BASE_URL}/rides/bookings/{booking_id}/accept",
        headers=auth_header(host_token),
        timeout=REQUEST_TIMEOUT,
    )
    if accept_res.status_code >= 400:
        return ride_id, booking_id, None

    requests.post(f"{BASE_URL}/rides/{ride_id}/start", headers=auth_header(host_token), timeout=REQUEST_TIMEOUT)
    requests.post(f"{BASE_URL}/rides/{ride_id}/end", headers=auth_header(host_token), timeout=REQUEST_TIMEOUT)
    settlement_res = requests.get(
        f"{BASE_URL}/settlements/booking/{booking_id}",
        headers=auth_header(rider_token),
        timeout=REQUEST_TIMEOUT,
    )
    settlement_id = None
    if settlement_res.status_code == 200 and settlement_res.json():
        settlement_id = settlement_res.json().get("SettlementID")
    return ride_id, booking_id, settlement_id


def admin_patch_row(admin_token: str, table_name: str, pk: int, payload: dict) -> bool:
    res = requests.patch(
        f"{BASE_URL}/admin/tables/{table_name}/{pk}",
        headers=auth_header(admin_token),
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    return res.status_code < 400


def admin_insert_row(admin_token: str, table_name: str, payload: dict) -> int | None:
    res = requests.post(
        f"{BASE_URL}/admin/tables/{table_name}",
        headers=auth_header(admin_token),
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    if res.status_code < 400:
        return res.json().get("id")
    return None


def create_review_ready_context(host_token: str, rider_token: str, admin_token: str) -> tuple[int | None, int | None]:
    ride_id, booking_id = create_pending_booking_pair(host_token, rider_token)
    if not ride_id or not booking_id:
        return None, None

    if admin_token:
        admin_patch_row(admin_token, "Bookings", booking_id, {"Booking_Status": "Confirmed"})
        admin_patch_row(admin_token, "Rides", ride_id, {"Ride_Status": "Completed"})

    return ride_id, booking_id


def create_settlement_ready_context(host_token: str, rider_token: str, admin_token: str) -> tuple[int | None, int | None, int | None]:
    ride_id, booking_id = create_review_ready_context(host_token, rider_token, admin_token)
    if not ride_id or not booking_id:
        return None, None, None

    settlement_id = None
    if admin_token:
        settlement_id = admin_insert_row(
            admin_token,
            "Cost_Settlements",
            {
                "BookingID": booking_id,
                "Calculated_Cost": "120.00",
                "Payment_Status": "Unpaid",
            },
        )

    return ride_id, booking_id, settlement_id


def choose_iterations(method: str, path: str) -> int:
    method = method.upper()
    if method == "GET":
        return READ_ITERATIONS

    one_shot_paths = {
        "/api/v1/rides/{ride_id}/start",
        "/api/v1/rides/{ride_id}/end",
        "/api/v1/rides/{ride_id}",
        "/api/v1/rides/{ride_id}/book",
        "/api/v1/rides/bookings/{booking_id}/accept",
        "/api/v1/rides/bookings/{booking_id}/reject",
        "/api/v1/rides/bookings/{booking_id}",
        "/api/v1/reviews",
        "/api/v1/reviews/{review_id}",
        "/api/v1/admin/tables/{table_name}",
        "/api/v1/admin/tables/{table_name}/{pk}",
    }
    if path in one_shot_paths or method == "DELETE":
        return STATEFUL_ITERATIONS
    return WRITE_ITERATIONS


def measure_api(
    name: str,
    method: str,
    url: str,
    iterations: int,
    headers: dict[str, str] | None = None,
    params: dict | None = None,
    json_producer=None,
    request_factory=None,
):
    latencies = []
    successes = 0
    last_response = None
    failures = []

    if method.upper() == "GET":
        try:
            if request_factory:
                warmup_req = request_factory()
                requests.request(
                    method,
                    warmup_req["url"],
                    headers=warmup_req.get("headers"),
                    params=warmup_req.get("params"),
                    json=warmup_req.get("json"),
                    timeout=REQUEST_TIMEOUT,
                )
            else:
                warmup_body = json_producer() if json_producer else None
                requests.request(method, url, headers=headers, params=params, json=warmup_body, timeout=REQUEST_TIMEOUT)
        except requests.RequestException:
            pass

    for _ in tqdm(range(iterations), desc=f"Processing {name}"):
        req_url = url
        req_headers = headers
        req_params = params
        body = json_producer() if json_producer else None

        if request_factory:
            req = request_factory()
            req_url = req["url"]
            req_headers = req.get("headers")
            req_params = req.get("params")
            body = req.get("json")

        start_time = time.time()
        try:
            response = requests.request(method, req_url, headers=req_headers, params=req_params, json=body, timeout=REQUEST_TIMEOUT)
            last_response = response
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)
            if response.status_code < 400:
                successes += 1
            elif len(failures) < 3:
                failures.append(f"{response.status_code}: {response.text[:160]}")
        except requests.exceptions.ConnectionError:
            print("FATAL ERROR: Could not connect to the backend")
            break
        except requests.RequestException as exc:
            if len(failures) < 3:
                failures.append(f"request_error: {exc}")
            continue

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0

    results[name] = {
        "method": method.upper(),
        "url": url.replace(BASE_URL, ""),
        "avg_ms": avg_latency,
        "max_ms": max_latency,
        "success": f"{successes}/{iterations}",
        "failures": failures,
    }
    print(f"{name:<70} | {avg_latency:>8.2f} ms | {successes}/{iterations} success")
    return last_response


def build_request_context(path: str, method: str) -> dict:
    admin_token = state["admin"]["token"]
    host_token = state["host"]["token"]
    rider_token = state["rider"]["token"]

    ctx = {
        "headers": None,
        "params": None,
        "json_producer": None,
        "request_factory": None,
        "path_values": {
            "member_id": state["rider"]["member_id"] or state["host"]["member_id"] or 1,
            "ride_id": state["open_ride_id"] or state["started_ride_id"] or state["completed_ride_id"] or 1,
            "booking_id": state["booking_settlement_id"] or state["booking_accept_id"] or 1,
            "settlement_id": state["settlement_id"] or 1,
            "location_id": state["location_id"] or 1,
            "address_id": state["saved_address_id"] or 1,
            "review_id": state["review_id"] or 1,
            "table_name": state["admin_table_name"],
            "pk": state["admin_inserted_pk"] or 1,
        },
    }

    if path.startswith("/api/v1/admin"):
        ctx["headers"] = auth_header(admin_token)
    elif path.startswith("/api/v1/auth"):
        ctx["headers"] = None
    elif path.startswith("/api/v1/health") or path.startswith("/api/v1/testing") or path.startswith("/api/v1/locations"):
        ctx["headers"] = None
    elif path.startswith("/api/v1/reviews"):
        ctx["headers"] = auth_header(rider_token)
    elif path.startswith("/api/v1/chat"):
        ctx["headers"] = auth_header(host_token)
    elif path.startswith("/api/v1/settlements"):
        ctx["headers"] = auth_header(rider_token)
    else:
        ctx["headers"] = auth_header(host_token)

    if path == "/api/v1/auth/register" and method == "POST":
        ctx["json_producer"] = lambda: {
            "username": f"profile_{random_string(8)}",
            "password": "password123!",
            "email": f"profile_{random_string(8)}@iitgn.ac.in",
            "full_name": "Profiled User",
            "phone_number": random_phone(),
            "gender": random.choice(["Male", "Female", "Other"]),
        }

    elif path == "/api/v1/auth/login" and method == "POST":
        login_users = state.get("login_users") or []
        ctx["json_producer"] = lambda: random.choice(login_users) if login_users else {
            "username": state["host"].get("username"),
            "password": "password123!",
        }

    elif path == "/api/v1/auth/me" and method == "GET":
        tokens = [token for token in [host_token, rider_token, admin_token] if token]
        chosen = random.choice(tokens) if tokens else host_token
        ctx["headers"] = auth_header(chosen)

    elif path == "/api/v1/rides" and method == "GET":
        ctx["params"] = {"only_open": random.choice([True, False]), "limit": random.randint(10, 100)}

    elif path == "/api/v1/rides" and method == "POST":
        ctx["headers"] = auth_header(host_token)
        ctx["json_producer"] = lambda: {
            "start_geohash": f"st{random_string(6)}",
            "end_geohash": f"en{random_string(6)}",
            "departure_time": (datetime.now() + timedelta(days=2, hours=2)).isoformat(),
            "vehicle_type": "Sedan",
            "max_capacity": 4,
            "base_fare_per_km": "14.50",
        }

    elif path == "/api/v1/rides/{ride_id}" and method == "PATCH":
        ctx["headers"] = auth_header(host_token)
        ctx["json_producer"] = lambda: {"vehicle_type": "SUV"}

    elif path == "/api/v1/rides/{ride_id}" and method == "DELETE":
        ctx["headers"] = auth_header(admin_token)
        def delete_ride_factory():
            ride_id = create_ride(admin_token) or state["delete_ride_id"] or 1
            return {
                "url": f"{BASE_URL}/rides/{ride_id}",
                "headers": auth_header(admin_token),
                "params": None,
                "json": None,
            }
        ctx["request_factory"] = delete_ride_factory

    elif path == "/api/v1/rides/{ride_id}/start" and method == "POST":
        ctx["headers"] = auth_header(host_token)
        def start_ride_factory():
            ride_id = create_ride(host_token) or state["lifecycle_ride_id"] or 1
            return {
                "url": f"{BASE_URL}/rides/{ride_id}/start",
                "headers": auth_header(host_token),
                "params": None,
                "json": None,
            }
        ctx["request_factory"] = start_ride_factory

    elif path == "/api/v1/rides/{ride_id}/with-bookings" and method == "GET":
        ctx["headers"] = auth_header(host_token)
        ctx["path_values"]["ride_id"] = state["lifecycle_ride_id"] or ctx["path_values"]["ride_id"]

    elif path == "/api/v1/rides/{ride_id}/end" and method == "POST":
        ctx["headers"] = auth_header(host_token)
        def end_ride_factory():
            ride_id = create_ride(host_token) or state["lifecycle_ride_id"] or 1
            if admin_token:
                admin_patch_row(admin_token, "Rides", ride_id, {"Ride_Status": "Started"})
            return {
                "url": f"{BASE_URL}/rides/{ride_id}/end",
                "headers": auth_header(host_token),
                "params": None,
                "json": None,
            }
        ctx["request_factory"] = end_ride_factory

    elif path == "/api/v1/rides/{ride_id}/book" and method == "POST":
        ctx["headers"] = auth_header(rider_token)
        def book_ride_factory():
            ride_id = create_ride(host_token) or state["open_ride_id"] or 1
            return {
                "url": f"{BASE_URL}/rides/{ride_id}/book",
                "headers": auth_header(rider_token),
                "params": None,
                "json": {"pickup_geohash": random_geohash("pk"), "drop_geohash": random_geohash("dp")},
            }
        ctx["request_factory"] = book_ride_factory

    elif path == "/api/v1/rides/my/bookings" and method == "GET":
        ctx["headers"] = auth_header(rider_token)

    elif path == "/api/v1/rides/{ride_id}/bookings/pending" and method == "GET":
        ctx["headers"] = auth_header(host_token)
        ctx["path_values"]["ride_id"] = state["open_ride_id"] or ctx["path_values"]["ride_id"]

    elif path == "/api/v1/rides/bookings/{booking_id}" and method == "DELETE":
        ctx["headers"] = auth_header(rider_token)
        def delete_booking_factory():
            _, booking_id = create_pending_booking_pair(host_token, rider_token)
            booking_id = booking_id or state["booking_delete_id"] or 1
            return {
                "url": f"{BASE_URL}/rides/bookings/{booking_id}",
                "headers": auth_header(rider_token),
                "params": None,
                "json": None,
            }
        ctx["request_factory"] = delete_booking_factory

    elif path == "/api/v1/rides/bookings/{booking_id}/accept" and method == "POST":
        ctx["headers"] = auth_header(host_token)
        def accept_booking_factory():
            _, booking_id = create_pending_booking_pair(host_token, rider_token)
            booking_id = booking_id or state["booking_accept_id"] or 1
            return {
                "url": f"{BASE_URL}/rides/bookings/{booking_id}/accept",
                "headers": auth_header(host_token),
                "params": None,
                "json": None,
            }
        ctx["request_factory"] = accept_booking_factory

    elif path == "/api/v1/rides/bookings/{booking_id}/reject" and method == "POST":
        ctx["headers"] = auth_header(host_token)
        def reject_booking_factory():
            _, booking_id = create_pending_booking_pair(host_token, rider_token)
            booking_id = booking_id or state["booking_reject_id"] or 1
            return {
                "url": f"{BASE_URL}/rides/bookings/{booking_id}/reject",
                "headers": auth_header(host_token),
                "params": None,
                "json": None,
            }
        ctx["request_factory"] = reject_booking_factory

    elif path == "/api/v1/locations" and method == "POST":
        ctx["json_producer"] = lambda: {
            "location_name": f"Loc {random_string(6)}",
            "location_type": random.choice(["Pickup", "Drop", "Transit"]),
            "geohash": f"gh{random_string(6)}",
        }

    elif path == "/api/v1/locations/{location_id}" and method == "GET":
        ctx["path_values"]["location_id"] = state["location_id"] or 1

    elif path == "/api/v1/preferences/me" and method == "GET":
        ctx["headers"] = auth_header(host_token)

    elif path == "/api/v1/preferences/me" and method == "PUT":
        ctx["headers"] = auth_header(host_token)
        ctx["json_producer"] = lambda: {
            "gender_preference": random.choice(["Any", "Same-Gender Only"]),
            "notify_on_new_ride": random.choice([True, False]),
            "music_preference": random.choice(["LoFi", "Classical", "None"]),
        }

    elif path == "/api/v1/reviews" and method == "POST":
        ctx["headers"] = auth_header(rider_token)
        def create_review_factory():
            ride_id, _ = create_review_ready_context(host_token, rider_token, admin_token)
            ride_id = ride_id or state["completed_ride_id"] or 1
            return {
                "url": f"{BASE_URL}/reviews",
                "headers": auth_header(rider_token),
                "params": None,
                "json": {
                    "ride_id": ride_id,
                    "reviewee_member_id": state["host"]["member_id"] or 1,
                    "rating": random.randint(3, 5),
                    "comments": f"Profiling review {random_string(6)}",
                },
            }
        ctx["request_factory"] = create_review_factory

    elif path == "/api/v1/reviews/ride/{ride_id}" and method == "GET":
        ctx["path_values"]["ride_id"] = state["completed_ride_id"] or ctx["path_values"]["ride_id"]

    elif path == "/api/v1/reviews/member/{member_id}" and method == "GET":
        ctx["path_values"]["member_id"] = state["host"]["member_id"] or ctx["path_values"]["member_id"]

    elif path == "/api/v1/reviews/{review_id}" and method == "DELETE":
        ctx["headers"] = auth_header(rider_token)
        def delete_review_factory():
            ride_id, _ = create_review_ready_context(host_token, rider_token, admin_token)
            ride_id = ride_id or state["completed_ride_id"] or 1
            review_res = requests.post(
                f"{BASE_URL}/reviews",
                headers=auth_header(rider_token),
                json={
                    "ride_id": ride_id,
                    "reviewee_member_id": state["host"]["member_id"] or 1,
                    "rating": random.randint(3, 5),
                    "comments": f"Delete review {random_string(6)}",
                },
                timeout=REQUEST_TIMEOUT,
            )
            review_id = state["review_id"] or 1
            if review_res.status_code == 201:
                review_id = review_res.json().get("ReviewID")
            return {
                "url": f"{BASE_URL}/reviews/{review_id}",
                "headers": auth_header(rider_token),
                "params": None,
                "json": None,
            }
        ctx["request_factory"] = delete_review_factory

    elif path == "/api/v1/settlements/{settlement_id}/status" and method == "PATCH":
        ctx["headers"] = auth_header(rider_token)
        def update_settlement_factory():
            _, _, settlement_id = create_settlement_ready_context(host_token, rider_token, admin_token)
            settlement_id = settlement_id or state["settlement_id"] or 1
            return {
                "url": f"{BASE_URL}/settlements/{settlement_id}/status",
                "headers": auth_header(rider_token),
                "params": None,
                "json": {"payment_status": random.choice(["Unpaid", "Settled"])},
            }
        ctx["request_factory"] = update_settlement_factory

    elif path == "/api/v1/settlements/booking/{booking_id}" and method == "GET":
        ctx["headers"] = auth_header(rider_token)
        ctx["path_values"]["booking_id"] = state["booking_settlement_id"] or ctx["path_values"]["booking_id"]

    elif path == "/api/v1/settlements/my" and method == "GET":
        ctx["headers"] = auth_header(rider_token)

    elif path == "/api/v1/chat/ride/{ride_id}" and method == "GET":
        ctx["headers"] = auth_header(host_token)
        ctx["path_values"]["ride_id"] = state["open_ride_id"] or ctx["path_values"]["ride_id"]

    elif path == "/api/v1/saved-addresses" and method == "GET":
        ctx["headers"] = auth_header(host_token)

    elif path == "/api/v1/saved-addresses" and method == "POST":
        ctx["headers"] = auth_header(host_token)
        ctx["json_producer"] = lambda: {
            "label": f"Addr {random_string(4)}",
            "location_id": state["location_id"] or 1,
        }

    elif path == "/api/v1/saved-addresses/{address_id}" and method == "PATCH":
        ctx["headers"] = auth_header(host_token)
        def update_saved_address_factory():
            location_id = create_location() or state["location_id"] or 1
            create_res = requests.post(
                f"{BASE_URL}/saved-addresses",
                headers=auth_header(host_token),
                json={"label": f"Addr {random_string(5)}", "location_id": location_id},
                timeout=REQUEST_TIMEOUT,
            )
            address_id = state["saved_address_id"] or 1
            if create_res.status_code == 201:
                address_id = create_res.json().get("AddressID")
            return {
                "url": f"{BASE_URL}/saved-addresses/{address_id}",
                "headers": auth_header(host_token),
                "params": None,
                "json": {"label": f"Updated {random_string(6)}"},
            }
        ctx["request_factory"] = update_saved_address_factory

    elif path == "/api/v1/saved-addresses/{address_id}" and method == "DELETE":
        ctx["headers"] = auth_header(host_token)
        def delete_saved_address_factory():
            location_id = create_location() or state["location_id"] or 1
            create_res = requests.post(
                f"{BASE_URL}/saved-addresses",
                headers=auth_header(host_token),
                json={"label": f"ToDelete {random_string(5)}", "location_id": location_id},
                timeout=REQUEST_TIMEOUT,
            )
            address_id = state["saved_address_id"] or 1
            if create_res.status_code == 201:
                address_id = create_res.json().get("AddressID")
            return {
                "url": f"{BASE_URL}/saved-addresses/{address_id}",
                "headers": auth_header(host_token),
                "params": None,
                "json": None,
            }
        ctx["request_factory"] = delete_saved_address_factory

    elif path == "/api/v1/admin/members/{member_id}/role" and method == "PATCH":
        ctx["json_producer"] = lambda: {"role": "user"}
        ctx["path_values"]["member_id"] = state["rider"]["member_id"] or ctx["path_values"]["member_id"]

    elif path == "/api/v1/admin/rides/{ride_id}/participants" and method == "GET":
        ctx["path_values"]["ride_id"] = state["open_ride_id"] or ctx["path_values"]["ride_id"]

    elif path == "/api/v1/admin/rides/{ride_id}/chats" and method == "GET":
        ctx["path_values"]["ride_id"] = state["open_ride_id"] or ctx["path_values"]["ride_id"]

    elif path == "/api/v1/admin/tables/{table_name}" and method == "GET":
        ctx["params"] = {"limit": 50, "offset": 0}

    elif path == "/api/v1/admin/tables/{table_name}" and method == "POST":
        ctx["json_producer"] = lambda: {
            "Location_Name": f"AdminLocation_{random_string(6)}",
            "Location_Type": "Pickup",
            "GeoHash": f"gh{random_string(6)}",
        }

    elif path == "/api/v1/admin/tables/{table_name}/{pk}" and method == "PATCH":
        def admin_patch_row_factory():
            create_res = requests.post(
                f"{BASE_URL}/admin/tables/{state['admin_table_name']}",
                headers=auth_header(admin_token),
                json={
                    "Location_Name": f"PatchRow_{random_string(6)}",
                    "Location_Type": "Pickup",
                    "GeoHash": random_geohash(),
                },
                timeout=REQUEST_TIMEOUT,
            )
            pk = state["admin_inserted_pk"] if state["admin_inserted_pk"] not in (None, -1) else 1
            if create_res.status_code < 400:
                pk = create_res.json().get("id", pk)
            return {
                "url": f"{BASE_URL}/admin/tables/{state['admin_table_name']}/{pk}",
                "headers": auth_header(admin_token),
                "params": None,
                "json": {"Location_Type": random.choice(["Transit", "Drop"])},
            }
        ctx["request_factory"] = admin_patch_row_factory

    elif path == "/api/v1/admin/tables/{table_name}/{pk}" and method == "DELETE":
        def admin_delete_row_factory():
            create_res = requests.post(
                f"{BASE_URL}/admin/tables/{state['admin_table_name']}",
                headers=auth_header(admin_token),
                json={
                    "Location_Name": f"DeleteRow_{random_string(6)}",
                    "Location_Type": "Pickup",
                    "GeoHash": random_geohash(),
                },
                timeout=REQUEST_TIMEOUT,
            )
            pk = state["admin_inserted_pk"] if state["admin_inserted_pk"] not in (None, -1) else 1
            if create_res.status_code < 400:
                pk = create_res.json().get("id", pk)
            return {
                "url": f"{BASE_URL}/admin/tables/{state['admin_table_name']}/{pk}",
                "headers": auth_header(admin_token),
                "params": None,
                "json": None,
            }
        ctx["request_factory"] = admin_delete_row_factory

    return ctx


def resolve_url(path_template: str, path_values: dict) -> str:
    path = path_template
    for key, value in path_values.items():
        path = path.replace(f"{{{key}}}", str(value))
    return f"{BASE_URL}{path.replace('/api/v1', '')}"


def post_process(path: str, method: str, response: requests.Response | None) -> None:
    if response is None or response.status_code >= 400:
        return

    if path == "/api/v1/admin/tables/{table_name}" and method == "POST":
        state["admin_inserted_pk"] = response.json().get("id")

    if path == "/api/v1/reviews" and method == "POST" and not state.get("review_id"):
        state["review_id"] = response.json().get("ReviewID")


def profile_all_endpoints() -> None:
    with open(SLIM_SPEC_PATH, "r", encoding="utf-8") as f:
        endpoints = json.load(f)

    print(f"--- Profiling {len(endpoints)} endpoints from {SLIM_SPEC_PATH.name} ---")
    for item in endpoints:
        path = item["path"]
        method = item["method"].upper()
        subsection = item.get("subsection", "unknown")

        ctx = build_request_context(path, method)
        url = resolve_url(path, ctx["path_values"])
        iterations = choose_iterations(method, path)
        name = f"{subsection} :: {method} {path}"

        response = measure_api(
            name=name,
            method=method,
            url=url,
            iterations=iterations,
            headers=ctx["headers"],
            params=ctx["params"],
            json_producer=ctx["json_producer"],
            request_factory=ctx["request_factory"],
        )
        post_process(path, method, response)


def export_results() -> None:
    print("\n=======================================================")
    print("          SUBSECTION-WISE API PROFILING REPORT         ")
    print("=======================================================")
    print(f"{'Endpoint (subsection::method path)':<72} | {'Avg ms':>10} | {'Max ms':>10}")
    print("-" * 102)

    sorted_results = sorted(results.items(), key=lambda x: x[1]["avg_ms"], reverse=True)
    for name, data in sorted_results:
        print(f"{name:<72} | {data['avg_ms']:>10.2f} | {data['max_ms']:>10.2f}")

    print("=" * 102)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    print(f"Saved detailed results to {RESULTS_PATH}")

    lines: list[str] = []
    lines.append("# API Profiling Results")
    lines.append("")
    lines.append(f"Generated at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")

    total_endpoints = len(results)
    success_endpoints = sum(1 for data in results.values() if data.get("success", "0/0").split("/")[0] == data.get("success", "0/0").split("/")[1])
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total endpoints profiled: **{total_endpoints}**")
    lines.append(f"- Endpoints with full success ratio: **{success_endpoints}/{total_endpoints}**")
    lines.append("")

    lines.append("## Top 10 Slowest Endpoints")
    lines.append("")
    lines.append("| Rank | Endpoint | Avg (ms) | Max (ms) | Success |")
    lines.append("|---:|---|---:|---:|---:|")
    top_10 = sorted(results.items(), key=lambda item: item[1].get("avg_ms", 0), reverse=True)[:10]
    for rank, (endpoint_name, data) in enumerate(top_10, start=1):
        avg_ms = float(data.get("avg_ms", 0))
        max_ms = float(data.get("max_ms", 0))
        success = str(data.get("success", "0/0"))
        lines.append(f"| {rank} | {endpoint_name} | {avg_ms:.2f} | {max_ms:.2f} | {success} |")
    lines.append("")

    subsection_buckets: dict[str, list[tuple[str, dict]]] = {}
    for endpoint_name, data in results.items():
        subsection = endpoint_name.split(" :: ", 1)[0]
        subsection_buckets.setdefault(subsection, []).append((endpoint_name, data))

    lines.append("## By Subsection")
    lines.append("")
    for subsection in sorted(subsection_buckets.keys()):
        lines.append(f"### {subsection}")
        lines.append("")
        lines.append("| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |")
        lines.append("|---|---|---|---:|---:|---:|")

        rows = sorted(subsection_buckets[subsection], key=lambda item: item[1]["avg_ms"], reverse=True)
        for endpoint_name, data in rows:
            url = str(data.get("url", ""))
            method = str(data.get("method", ""))
            avg_ms = float(data.get("avg_ms", 0))
            max_ms = float(data.get("max_ms", 0))
            success = str(data.get("success", "0/0"))
            endpoint_label = endpoint_name.split(" :: ", 1)[1] if " :: " in endpoint_name else endpoint_name
            lines.append(f"| {endpoint_label} | {method} | {url} | {avg_ms:.2f} | {max_ms:.2f} | {success} |")

        subsection_failures = []
        for endpoint_name, data in rows:
            failures = data.get("failures") or []
            if failures:
                subsection_failures.append((endpoint_name, failures))

        if subsection_failures:
            lines.append("")
            lines.append("**Sample failures:**")
            for endpoint_name, failures in subsection_failures:
                lines.append(f"- {endpoint_name}")
                for failure in failures[:2]:
                    sanitized = str(failure).replace("\n", " ").strip()
                    lines.append(f"  - {sanitized}")

        lines.append("")

    with open(MARKDOWN_RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Saved markdown report to {MARKDOWN_RESULTS_PATH}")


if __name__ == "__main__":
    try:
        bootstrap_state()
        profile_all_endpoints()
        export_results()
    except KeyboardInterrupt:
        print("\nProfiling aborted by user.")
    except Exception as exc:
        print(f"\nProfiling failed: {exc}")