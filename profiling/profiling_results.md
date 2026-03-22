# API Profiling Results

Generated at: 2026-03-22T14:52:15

## Summary

- Total endpoints profiled: **50**
- Endpoints with full success ratio: **47/50**

## Top 10 Slowest Endpoints

| Rank | Endpoint | Avg (ms) | Max (ms) | Success |
|---:|---|---:|---:|---:|
| 1 | admin :: GET /api/v1/admin/members | 2697.57 | 2864.70 | 20/20 |
| 2 | auth :: POST /api/v1/auth/register | 269.85 | 319.06 | 20/20 |
| 3 | auth :: POST /api/v1/auth/login | 247.66 | 254.55 | 20/20 |
| 4 | admin :: GET /api/v1/admin/rides/open | 224.83 | 352.30 | 20/20 |
| 5 | admin :: GET /api/v1/admin/rides/completed | 223.49 | 310.12 | 20/20 |
| 6 | admin :: GET /api/v1/admin/rides/stats | 71.97 | 78.63 | 20/20 |
| 7 | admin :: GET /api/v1/admin/audit-logs | 32.65 | 40.71 | 20/20 |
| 8 | settlements :: GET /api/v1/settlements/my | 24.28 | 25.88 | 20/20 |
| 9 | rides :: POST /api/v1/rides | 19.04 | 44.29 | 20/20 |
| 10 | bookings :: POST /api/v1/rides/bookings/{booking_id}/accept | 16.74 | 22.60 | 0/20 |

## By Subsection

### admin

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/admin/members | GET | /admin/members | 2697.57 | 2864.70 | 20/20 |
| GET /api/v1/admin/rides/open | GET | /admin/rides/open | 224.83 | 352.30 | 20/20 |
| GET /api/v1/admin/rides/completed | GET | /admin/rides/completed | 223.49 | 310.12 | 20/20 |
| GET /api/v1/admin/rides/stats | GET | /admin/rides/stats | 71.97 | 78.63 | 20/20 |
| GET /api/v1/admin/audit-logs | GET | /admin/audit-logs | 32.65 | 40.71 | 20/20 |
| POST /api/v1/admin/tables/{table_name} | POST | /admin/tables/Locations | 15.36 | 48.18 | 20/20 |
| PATCH /api/v1/admin/tables/{table_name}/{pk} | PATCH | /admin/tables/Locations/1051 | 13.38 | 15.99 | 20/20 |
| DELETE /api/v1/admin/tables/{table_name}/{pk} | DELETE | /admin/tables/Locations/1051 | 12.43 | 13.38 | 20/20 |
| GET /api/v1/admin/tables/{table_name} | GET | /admin/tables/Locations | 10.14 | 12.46 | 20/20 |
| PATCH /api/v1/admin/members/{member_id}/role | PATCH | /admin/members/20028/role | 8.13 | 9.13 | 20/20 |
| GET /api/v1/admin/rides/{ride_id}/participants | GET | /admin/rides/20026/participants | 7.40 | 8.89 | 20/20 |
| GET /api/v1/admin/rides/{ride_id}/chats | GET | /admin/rides/20026/chats | 7.11 | 8.33 | 20/20 |
| GET /api/v1/admin/tables | GET | /admin/tables | 6.44 | 7.86 | 20/20 |
| GET /api/v1/admin/rides/active | GET | /admin/rides/active | 5.69 | 6.66 | 20/20 |

### auth

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/auth/register | POST | /auth/register | 269.85 | 319.06 | 20/20 |
| POST /api/v1/auth/login | POST | /auth/login | 247.66 | 254.55 | 20/20 |
| GET /api/v1/auth/me | GET | /auth/me | 5.68 | 6.74 | 20/20 |

### bookings

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/rides/bookings/{booking_id}/accept | POST | /rides/bookings/30061/accept | 16.74 | 22.60 | 0/20 |
| POST /api/v1/rides/{ride_id}/book | POST | /rides/20026/book | 12.48 | 13.56 | 20/20 |
| POST /api/v1/rides/bookings/{booking_id}/reject | POST | /rides/bookings/30061/reject | 12.02 | 12.71 | 20/20 |
| DELETE /api/v1/rides/bookings/{booking_id} | DELETE | /rides/bookings/30061 | 11.37 | 11.95 | 20/20 |
| GET /api/v1/rides/{ride_id}/bookings/pending | GET | /rides/20026/bookings/pending | 8.12 | 9.22 | 20/20 |
| GET /api/v1/rides/my/bookings | GET | /rides/my/bookings | 8.07 | 9.51 | 20/20 |

**Sample failures:**
- bookings :: POST /api/v1/rides/bookings/{booking_id}/accept
  - 500: Internal Server Error
  - 500: Internal Server Error

### chat

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/chat/ride/{ride_id} | GET | /chat/ride/20026 | 7.23 | 7.94 | 20/20 |

### locations

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/locations | POST | /locations | 9.48 | 24.92 | 20/20 |
| GET /api/v1/locations | GET | /locations | 7.08 | 8.11 | 20/20 |
| GET /api/v1/locations/{location_id} | GET | /locations/1031 | 5.18 | 7.88 | 20/20 |

### preferences

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| PUT /api/v1/preferences/me | PUT | /preferences/me | 11.80 | 22.01 | 20/20 |
| GET /api/v1/preferences/me | GET | /preferences/me | 6.67 | 7.42 | 20/20 |

### reviews

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/reviews | POST | /reviews | 13.57 | 14.82 | 20/20 |
| DELETE /api/v1/reviews/{review_id} | DELETE | /reviews/15059 | 10.98 | 11.87 | 20/20 |
| GET /api/v1/reviews/member/{member_id} | GET | /reviews/member/20027 | 10.50 | 16.27 | 20/20 |
| GET /api/v1/reviews/my | GET | /reviews/my | 8.72 | 10.11 | 20/20 |
| GET /api/v1/reviews/ride/{ride_id} | GET | /reviews/ride/20029 | 6.87 | 7.54 | 20/20 |

### rides

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| POST /api/v1/rides | POST | /rides | 19.04 | 44.29 | 20/20 |
| POST /api/v1/rides/{ride_id}/start | POST | /rides/20026/start | 15.40 | 32.11 | 0/20 |
| PATCH /api/v1/rides/{ride_id} | PATCH | /rides/20026 | 11.15 | 17.13 | 20/20 |
| DELETE /api/v1/rides/{ride_id} | DELETE | /rides/20026 | 10.19 | 11.45 | 20/20 |
| GET /api/v1/rides/{ride_id}/with-bookings | GET | /rides/20027/with-bookings | 9.15 | 15.18 | 20/20 |
| POST /api/v1/rides/{ride_id}/end | POST | /rides/20026/end | 7.49 | 9.34 | 0/20 |
| GET /api/v1/rides | GET | /rides | 6.81 | 7.41 | 20/20 |

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
| POST /api/v1/saved-addresses | POST | /saved-addresses | 10.93 | 19.60 | 20/20 |
| PATCH /api/v1/saved-addresses/{address_id} | PATCH | /saved-addresses/26 | 10.49 | 11.18 | 20/20 |
| DELETE /api/v1/saved-addresses/{address_id} | DELETE | /saved-addresses/26 | 9.33 | 10.04 | 20/20 |
| GET /api/v1/saved-addresses | GET | /saved-addresses | 8.58 | 15.69 | 20/20 |

### settlements

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/settlements/my | GET | /settlements/my | 24.28 | 25.88 | 20/20 |
| PATCH /api/v1/settlements/{settlement_id}/status | PATCH | /settlements/1/status | 11.13 | 20.37 | 20/20 |
| GET /api/v1/settlements/booking/{booking_id} | GET | /settlements/booking/30061 | 7.11 | 7.93 | 20/20 |

### testing

| Endpoint | Method | URL | Avg (ms) | Max (ms) | Success |
|---|---|---|---:|---:|---:|
| GET /api/v1/testing/db | GET | /testing/db | 3.60 | 4.24 | 20/20 |
| GET /api/v1/health | GET | /health | 2.00 | 2.87 | 20/20 |

