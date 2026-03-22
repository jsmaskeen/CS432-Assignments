# API Profiling Results

Generated at: 2026-03-22T12:56:28

## Summary

- Total endpoints profiled: **50**
- Endpoints with full success ratio: **47/50**

## Top 10 Slowest Endpoints

| Rank | Endpoint | Avg (ms) | Max (ms) | Success |
|---:|---|---:|---:|---:|
| 1 | admin :: GET /api/v1/admin/members | 2770.09 | 2890.06 | 20/20 |
| 2 | auth :: POST /api/v1/auth/register | 269.40 | 308.78 | 20/20 |
| 3 | auth :: POST /api/v1/auth/login | 252.43 | 268.56 | 20/20 |
| 4 | admin :: GET /api/v1/admin/rides/completed | 209.72 | 286.58 | 20/20 |
| 5 | admin :: GET /api/v1/admin/rides/open | 207.64 | 293.19 | 20/20 |
| 6 | admin :: GET /api/v1/admin/rides/stats | 72.85 | 78.37 | 20/20 |
| 7 | admin :: GET /api/v1/admin/audit-logs | 30.13 | 50.12 | 20/20 |
| 8 | settlements :: GET /api/v1/settlements/my | 26.29 | 29.08 | 20/20 |
| 9 | rides :: POST /api/v1/rides | 17.55 | 27.74 | 20/20 |
| 10 | bookings :: POST /api/v1/rides/bookings/{booking_id}/accept | 17.41 | 36.32 | 0/20 |

## By Subsection

### admin

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/admin/members | GET | /admin/members | 2770.09 | 2890.06 | 20/20 |
| GET /api/v1/admin/rides/completed | GET | /admin/rides/completed | 209.72 | 286.58 | 20/20 |
| GET /api/v1/admin/rides/open | GET | /admin/rides/open | 207.64 | 293.19 | 20/20 |
| GET /api/v1/admin/rides/stats | GET | /admin/rides/stats | 72.85 | 78.37 | 20/20 |
| GET /api/v1/admin/audit-logs | GET | /admin/audit-logs | 30.13 | 50.12 | 20/20 |
| DELETE /api/v1/admin/tables/{table_name}/{pk} | DELETE | /admin/tables/Locations/1051 | 13.98 | 32.19 | 20/20 |
| POST /api/v1/admin/tables/{table_name} | POST | /admin/tables/Locations | 13.46 | 28.79 | 20/20 |
| PATCH /api/v1/admin/tables/{table_name}/{pk} | PATCH | /admin/tables/Locations/1051 | 12.19 | 12.83 | 20/20 |
| GET /api/v1/admin/tables/{table_name} | GET | /admin/tables/Locations | 10.87 | 12.54 | 20/20 |
| GET /api/v1/admin/rides/{ride_id}/participants | GET | /admin/rides/20026/participants | 9.68 | 14.80 | 20/20 |
| PATCH /api/v1/admin/members/{member_id}/role | PATCH | /admin/members/20028/role | 8.74 | 10.11 | 20/20 |
| GET /api/v1/admin/rides/{ride_id}/chats | GET | /admin/rides/20026/chats | 7.83 | 8.36 | 20/20 |
| GET /api/v1/admin/tables | GET | /admin/tables | 6.81 | 7.95 | 20/20 |
| GET /api/v1/admin/rides/active | GET | /admin/rides/active | 6.03 | 7.17 | 20/20 |

### auth

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/auth/register | POST | /auth/register | 269.40 | 308.78 | 20/20 |
| POST /api/v1/auth/login | POST | /auth/login | 252.43 | 268.56 | 20/20 |
| GET /api/v1/auth/me | GET | /auth/me | 7.92 | 12.06 | 20/20 |

### bookings

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/rides/bookings/{booking_id}/accept | POST | /rides/bookings/30061/accept | 17.41 | 36.32 | 0/20 |
| POST /api/v1/rides/bookings/{booking_id}/reject | POST | /rides/bookings/30061/reject | 12.58 | 13.52 | 20/20 |
| DELETE /api/v1/rides/bookings/{booking_id} | DELETE | /rides/bookings/30061 | 12.47 | 16.63 | 20/20 |
| POST /api/v1/rides/{ride_id}/book | POST | /rides/20026/book | 12.29 | 16.60 | 20/20 |
| GET /api/v1/rides/{ride_id}/bookings/pending | GET | /rides/20026/bookings/pending | 8.27 | 10.45 | 20/20 |
| GET /api/v1/rides/my/bookings | GET | /rides/my/bookings | 7.66 | 8.58 | 20/20 |

**Sample failures:**
- bookings :: POST /api/v1/rides/bookings/{booking_id}/accept
  - 500: Internal Server Error
  - 500: Internal Server Error

### chat

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/chat/ride/{ride_id} | GET | /chat/ride/20026 | 7.62 | 8.46 | 20/20 |

### locations

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/locations | POST | /locations | 7.59 | 12.39 | 20/20 |
| GET /api/v1/locations | GET | /locations | 7.19 | 8.56 | 20/20 |
| GET /api/v1/locations/{location_id} | GET | /locations/1031 | 4.31 | 5.43 | 20/20 |

### preferences

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| PUT /api/v1/preferences/me | PUT | /preferences/me | 13.80 | 26.39 | 20/20 |
| GET /api/v1/preferences/me | GET | /preferences/me | 6.54 | 7.36 | 20/20 |

### reviews

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/reviews | POST | /reviews | 13.77 | 15.38 | 20/20 |
| DELETE /api/v1/reviews/{review_id} | DELETE | /reviews/15059 | 11.78 | 22.49 | 20/20 |
| GET /api/v1/reviews/member/{member_id} | GET | /reviews/member/20027 | 10.99 | 25.54 | 20/20 |
| GET /api/v1/reviews/my | GET | /reviews/my | 8.58 | 9.90 | 20/20 |
| GET /api/v1/reviews/ride/{ride_id} | GET | /reviews/ride/20029 | 6.81 | 7.88 | 20/20 |

### rides

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/rides | POST | /rides | 17.55 | 27.74 | 20/20 |
| POST /api/v1/rides/{ride_id}/start | POST | /rides/20026/start | 16.41 | 26.36 | 0/20 |
| GET /api/v1/rides | GET | /rides | 10.14 | 10.83 | 20/20 |
| PATCH /api/v1/rides/{ride_id} | PATCH | /rides/20026 | 9.81 | 12.52 | 20/20 |
| DELETE /api/v1/rides/{ride_id} | DELETE | /rides/20026 | 9.75 | 10.91 | 20/20 |
| GET /api/v1/rides/{ride_id}/with-bookings | GET | /rides/20027/with-bookings | 7.69 | 9.02 | 20/20 |
| POST /api/v1/rides/{ride_id}/end | POST | /rides/20026/end | 7.34 | 7.93 | 0/20 |

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
| POST /api/v1/saved-addresses | POST | /saved-addresses | 10.92 | 21.37 | 20/20 |
| DELETE /api/v1/saved-addresses/{address_id} | DELETE | /saved-addresses/26 | 10.79 | 19.62 | 20/20 |
| PATCH /api/v1/saved-addresses/{address_id} | PATCH | /saved-addresses/26 | 10.35 | 13.31 | 20/20 |
| GET /api/v1/saved-addresses | GET | /saved-addresses | 5.81 | 6.48 | 20/20 |

### settlements

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/settlements/my | GET | /settlements/my | 26.29 | 29.08 | 20/20 |
| PATCH /api/v1/settlements/{settlement_id}/status | PATCH | /settlements/1/status | 11.31 | 13.25 | 20/20 |
| GET /api/v1/settlements/booking/{booking_id} | GET | /settlements/booking/30061 | 9.04 | 13.44 | 20/20 |

### testing

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/testing/db | GET | /testing/db | 3.79 | 4.51 | 20/20 |
| GET /api/v1/health | GET | /health | 2.26 | 2.94 | 20/20 |

