# API Profiling Results

Generated at: 2026-03-22T12:54:31

## Summary

- Total endpoints profiled: **50**
- Endpoints with full success ratio: **47/50**

## Top 10 Slowest Endpoints

| Rank | Endpoint | Avg (ms) | Max (ms) | Success |
|---:|---|---:|---:|---:|
| 1 | admin :: GET /api/v1/admin/members | 2642.95 | 2820.27 | 20/20 |
| 2 | auth :: POST /api/v1/auth/register | 268.55 | 300.81 | 20/20 |
| 3 | auth :: POST /api/v1/auth/login | 253.97 | 299.94 | 20/20 |
| 4 | admin :: GET /api/v1/admin/rides/completed | 219.39 | 328.07 | 20/20 |
| 5 | admin :: GET /api/v1/admin/rides/open | 217.33 | 286.91 | 20/20 |
| 6 | admin :: GET /api/v1/admin/rides/stats | 95.85 | 133.17 | 20/20 |
| 7 | admin :: GET /api/v1/admin/audit-logs | 30.37 | 34.05 | 20/20 |
| 8 | settlements :: GET /api/v1/settlements/my | 25.07 | 26.27 | 20/20 |
| 9 | rides :: GET /api/v1/rides | 22.62 | 23.32 | 20/20 |
| 10 | admin :: GET /api/v1/admin/rides/active | 18.64 | 20.18 | 20/20 |

## By Subsection

### admin

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/admin/members | GET | /admin/members | 2642.95 | 2820.27 | 20/20 |
| GET /api/v1/admin/rides/completed | GET | /admin/rides/completed | 219.39 | 328.07 | 20/20 |
| GET /api/v1/admin/rides/open | GET | /admin/rides/open | 217.33 | 286.91 | 20/20 |
| GET /api/v1/admin/rides/stats | GET | /admin/rides/stats | 95.85 | 133.17 | 20/20 |
| GET /api/v1/admin/audit-logs | GET | /admin/audit-logs | 30.37 | 34.05 | 20/20 |
| GET /api/v1/admin/rides/active | GET | /admin/rides/active | 18.64 | 20.18 | 20/20 |
| PATCH /api/v1/admin/tables/{table_name}/{pk} | PATCH | /admin/tables/Locations/1051 | 13.62 | 23.05 | 20/20 |
| DELETE /api/v1/admin/tables/{table_name}/{pk} | DELETE | /admin/tables/Locations/1051 | 13.17 | 14.55 | 20/20 |
| POST /api/v1/admin/tables/{table_name} | POST | /admin/tables/Locations | 12.66 | 18.44 | 20/20 |
| GET /api/v1/admin/tables/{table_name} | GET | /admin/tables/Locations | 10.29 | 11.25 | 20/20 |
| PATCH /api/v1/admin/members/{member_id}/role | PATCH | /admin/members/20028/role | 9.03 | 10.11 | 20/20 |
| GET /api/v1/admin/rides/{ride_id}/chats | GET | /admin/rides/20026/chats | 7.57 | 8.90 | 20/20 |
| GET /api/v1/admin/rides/{ride_id}/participants | GET | /admin/rides/20026/participants | 7.44 | 8.44 | 20/20 |
| GET /api/v1/admin/tables | GET | /admin/tables | 6.71 | 7.72 | 20/20 |

### auth

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/auth/register | POST | /auth/register | 268.55 | 300.81 | 20/20 |
| POST /api/v1/auth/login | POST | /auth/login | 253.97 | 299.94 | 20/20 |
| GET /api/v1/auth/me | GET | /auth/me | 5.59 | 6.52 | 20/20 |

### bookings

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/rides/bookings/{booking_id}/accept | POST | /rides/bookings/30061/accept | 16.81 | 25.60 | 0/20 |
| POST /api/v1/rides/bookings/{booking_id}/reject | POST | /rides/bookings/30061/reject | 13.08 | 28.97 | 20/20 |
| POST /api/v1/rides/{ride_id}/book | POST | /rides/20026/book | 12.95 | 20.69 | 20/20 |
| DELETE /api/v1/rides/bookings/{booking_id} | DELETE | /rides/bookings/30061 | 11.73 | 12.54 | 20/20 |
| GET /api/v1/rides/{ride_id}/bookings/pending | GET | /rides/20026/bookings/pending | 8.41 | 9.66 | 20/20 |
| GET /api/v1/rides/my/bookings | GET | /rides/my/bookings | 8.14 | 8.82 | 20/20 |

**Sample failures:**
- bookings :: POST /api/v1/rides/bookings/{booking_id}/accept
  - 500: Internal Server Error
  - 500: Internal Server Error

### chat

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/chat/ride/{ride_id} | GET | /chat/ride/20026 | 7.44 | 8.38 | 20/20 |

### locations

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/locations | POST | /locations | 7.76 | 8.57 | 20/20 |
| GET /api/v1/locations | GET | /locations | 7.65 | 8.42 | 20/20 |
| GET /api/v1/locations/{location_id} | GET | /locations/1031 | 4.45 | 5.48 | 20/20 |

### preferences

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| PUT /api/v1/preferences/me | PUT | /preferences/me | 10.96 | 12.13 | 20/20 |
| GET /api/v1/preferences/me | GET | /preferences/me | 6.63 | 7.43 | 20/20 |

### reviews

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/reviews | POST | /reviews | 14.40 | 25.01 | 20/20 |
| DELETE /api/v1/reviews/{review_id} | DELETE | /reviews/15059 | 10.88 | 11.99 | 20/20 |
| GET /api/v1/reviews/member/{member_id} | GET | /reviews/member/20027 | 8.37 | 9.05 | 20/20 |
| GET /api/v1/reviews/my | GET | /reviews/my | 7.93 | 9.75 | 20/20 |
| GET /api/v1/reviews/ride/{ride_id} | GET | /reviews/ride/20029 | 6.94 | 7.69 | 20/20 |

### rides

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/rides | GET | /rides | 22.62 | 23.32 | 20/20 |
| POST /api/v1/rides | POST | /rides | 17.10 | 29.99 | 20/20 |
| POST /api/v1/rides/{ride_id}/start | POST | /rides/20026/start | 16.85 | 37.50 | 0/20 |
| DELETE /api/v1/rides/{ride_id} | DELETE | /rides/20026 | 9.79 | 10.67 | 20/20 |
| PATCH /api/v1/rides/{ride_id} | PATCH | /rides/20026 | 9.14 | 12.56 | 20/20 |
| POST /api/v1/rides/{ride_id}/end | POST | /rides/20026/end | 7.70 | 12.70 | 0/20 |
| GET /api/v1/rides/{ride_id}/with-bookings | GET | /rides/20027/with-bookings | 7.63 | 9.08 | 20/20 |

**Sample failures:**
- rides :: POST /api/v1/rides/{ride_id}/start
  - 500: Internal Server Error
  - 500: Internal Server Error
- rides :: POST /api/v1/rides/{ride_id}/end
  - 400: {"detail":"Ride is not started"}
  - 400: {"detail":"Ride is not started"}

### saved-addresses

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/saved-addresses | POST | /saved-addresses | 12.95 | 21.99 | 20/20 |
| PATCH /api/v1/saved-addresses/{address_id} | PATCH | /saved-addresses/26 | 10.68 | 12.10 | 20/20 |
| DELETE /api/v1/saved-addresses/{address_id} | DELETE | /saved-addresses/26 | 9.61 | 11.56 | 20/20 |
| GET /api/v1/saved-addresses | GET | /saved-addresses | 5.85 | 6.86 | 20/20 |

### settlements

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/settlements/my | GET | /settlements/my | 25.07 | 26.27 | 20/20 |
| PATCH /api/v1/settlements/{settlement_id}/status | PATCH | /settlements/1/status | 10.94 | 20.88 | 20/20 |
| GET /api/v1/settlements/booking/{booking_id} | GET | /settlements/booking/30061 | 7.49 | 8.47 | 20/20 |

### testing

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/testing/db | GET | /testing/db | 3.81 | 4.49 | 20/20 |
| GET /api/v1/health | GET | /health | 2.19 | 2.75 | 20/20 |

