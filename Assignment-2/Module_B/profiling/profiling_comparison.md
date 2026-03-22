# Profiling Comparison (Before vs After Indexing)

- Before file: profiling_results_before.json
- After file: profiling_results_after.json
- Endpoints compared: 50
- Improved: 26
- Regressed: 24
- Unchanged: 0

## Top 15 Improvements

| Endpoint | Before Avg (ms) | After Avg (ms) | Delta (ms) | Improvement % | Before Success | After Success |
|---|---:|---:|---:|---:|---:|---:|
| admin :: GET /api/v1/admin/rides/active | 18.64 | 6.03 | 12.61 | 67.63% | 20/20 | 20/20 |
| rides :: GET /api/v1/rides | 22.62 | 10.14 | 12.48 | 55.19% | 20/20 | 20/20 |
| admin :: GET /api/v1/admin/rides/stats | 95.85 | 72.85 | 23.00 | 23.99% | 20/20 | 20/20 |
| saved-addresses :: POST /api/v1/saved-addresses | 12.95 | 10.92 | 2.03 | 15.68% | 20/20 | 20/20 |
| admin :: PATCH /api/v1/admin/tables/{table_name}/{pk} | 13.62 | 12.19 | 1.43 | 10.50% | 20/20 | 20/20 |
| bookings :: GET /api/v1/rides/my/bookings | 8.14 | 7.66 | 0.49 | 5.98% | 20/20 | 20/20 |
| locations :: GET /api/v1/locations | 7.65 | 7.19 | 0.46 | 5.96% | 20/20 | 20/20 |
| bookings :: POST /api/v1/rides/{ride_id}/book | 12.95 | 12.29 | 0.66 | 5.10% | 20/20 | 20/20 |
| rides :: POST /api/v1/rides/{ride_id}/end | 7.70 | 7.34 | 0.36 | 4.64% | 0/20 | 0/20 |
| admin :: GET /api/v1/admin/rides/open | 217.33 | 207.64 | 9.68 | 4.45% | 20/20 | 20/20 |
| admin :: GET /api/v1/admin/rides/completed | 219.39 | 209.72 | 9.67 | 4.41% | 20/20 | 20/20 |
| reviews :: POST /api/v1/reviews | 14.40 | 13.77 | 0.63 | 4.37% | 20/20 | 20/20 |
| bookings :: POST /api/v1/rides/bookings/{booking_id}/reject | 13.08 | 12.58 | 0.51 | 3.88% | 20/20 | 20/20 |
| locations :: GET /api/v1/locations/{location_id} | 4.45 | 4.31 | 0.14 | 3.25% | 20/20 | 20/20 |
| admin :: PATCH /api/v1/admin/members/{member_id}/role | 9.03 | 8.74 | 0.29 | 3.21% | 20/20 | 20/20 |

## Full Endpoint Comparison

| Endpoint | Method | URL | Before Avg | After Avg | Delta | Improve % | Before Max | After Max |
|---|---|---|---:|---:|---:|---:|---:|---:|
| admin :: GET /api/v1/admin/rides/active | GET | /admin/rides/active | 18.64 | 6.03 | 12.61 | 67.63% | 20.18 | 7.17 |
| rides :: GET /api/v1/rides | GET | /rides | 22.62 | 10.14 | 12.48 | 55.19% | 23.32 | 10.83 |
| admin :: GET /api/v1/admin/rides/stats | GET | /admin/rides/stats | 95.85 | 72.85 | 23.00 | 23.99% | 133.17 | 78.37 |
| saved-addresses :: POST /api/v1/saved-addresses | POST | /saved-addresses | 12.95 | 10.92 | 2.03 | 15.68% | 21.99 | 21.37 |
| admin :: PATCH /api/v1/admin/tables/{table_name}/{pk} | PATCH | /admin/tables/Locations/1051 | 13.62 | 12.19 | 1.43 | 10.50% | 23.05 | 12.83 |
| bookings :: GET /api/v1/rides/my/bookings | GET | /rides/my/bookings | 8.14 | 7.66 | 0.49 | 5.98% | 8.82 | 8.58 |
| locations :: GET /api/v1/locations | GET | /locations | 7.65 | 7.19 | 0.46 | 5.96% | 8.42 | 8.56 |
| bookings :: POST /api/v1/rides/{ride_id}/book | POST | /rides/20026/book | 12.95 | 12.29 | 0.66 | 5.10% | 20.69 | 16.60 |
| rides :: POST /api/v1/rides/{ride_id}/end | POST | /rides/20026/end | 7.70 | 7.34 | 0.36 | 4.64% | 12.70 | 7.93 |
| admin :: GET /api/v1/admin/rides/open | GET | /admin/rides/open | 217.33 | 207.64 | 9.68 | 4.45% | 286.91 | 293.19 |
| admin :: GET /api/v1/admin/rides/completed | GET | /admin/rides/completed | 219.39 | 209.72 | 9.67 | 4.41% | 328.07 | 286.58 |
| reviews :: POST /api/v1/reviews | POST | /reviews | 14.40 | 13.77 | 0.63 | 4.37% | 25.01 | 15.38 |
| bookings :: POST /api/v1/rides/bookings/{booking_id}/reject | POST | /rides/bookings/30061/reject | 13.08 | 12.58 | 0.51 | 3.88% | 28.97 | 13.52 |
| locations :: GET /api/v1/locations/{location_id} | GET | /locations/1031 | 4.45 | 4.31 | 0.14 | 3.25% | 5.48 | 5.43 |
| admin :: PATCH /api/v1/admin/members/{member_id}/role | PATCH | /admin/members/20028/role | 9.03 | 8.74 | 0.29 | 3.21% | 10.11 | 10.11 |
| saved-addresses :: PATCH /api/v1/saved-addresses/{address_id} | PATCH | /saved-addresses/26 | 10.68 | 10.35 | 0.33 | 3.13% | 12.10 | 13.31 |
| rides :: POST /api/v1/rides/{ride_id}/start | POST | /rides/20026/start | 16.85 | 16.41 | 0.44 | 2.60% | 37.50 | 26.36 |
| locations :: POST /api/v1/locations | POST | /locations | 7.76 | 7.59 | 0.16 | 2.13% | 8.57 | 12.39 |
| reviews :: GET /api/v1/reviews/ride/{ride_id} | GET | /reviews/ride/20029 | 6.94 | 6.81 | 0.13 | 1.86% | 7.69 | 7.88 |
| bookings :: GET /api/v1/rides/{ride_id}/bookings/pending | GET | /rides/20026/bookings/pending | 8.41 | 8.27 | 0.13 | 1.60% | 9.66 | 10.45 |
| preferences :: GET /api/v1/preferences/me | GET | /preferences/me | 6.63 | 6.54 | 0.08 | 1.26% | 7.43 | 7.36 |
| admin :: GET /api/v1/admin/audit-logs | GET | /admin/audit-logs | 30.37 | 30.13 | 0.24 | 0.78% | 34.05 | 50.12 |
| saved-addresses :: GET /api/v1/saved-addresses | GET | /saved-addresses | 5.85 | 5.81 | 0.04 | 0.62% | 6.86 | 6.48 |
| auth :: POST /api/v1/auth/login | POST | /auth/login | 253.97 | 252.43 | 1.54 | 0.61% | 299.94 | 268.56 |
| testing :: GET /api/v1/testing/db | GET | /testing/db | 3.81 | 3.79 | 0.02 | 0.49% | 4.49 | 4.51 |
| rides :: DELETE /api/v1/rides/{ride_id} | DELETE | /rides/20026 | 9.79 | 9.75 | 0.04 | 0.41% | 10.67 | 10.91 |
| auth :: POST /api/v1/auth/register | POST | /auth/register | 268.55 | 269.40 | -0.86 | -0.32% | 300.81 | 308.78 |
| rides :: GET /api/v1/rides/{ride_id}/with-bookings | GET | /rides/20027/with-bookings | 7.63 | 7.69 | -0.06 | -0.75% | 9.08 | 9.02 |
| admin :: GET /api/v1/admin/tables | GET | /admin/tables | 6.71 | 6.81 | -0.10 | -1.47% | 7.72 | 7.95 |
| chat :: GET /api/v1/chat/ride/{ride_id} | GET | /chat/ride/20026 | 7.44 | 7.62 | -0.18 | -2.38% | 8.38 | 8.46 |
| rides :: POST /api/v1/rides | POST | /rides | 17.10 | 17.55 | -0.45 | -2.65% | 29.99 | 27.74 |
| testing :: GET /api/v1/health | GET | /health | 2.19 | 2.26 | -0.06 | -2.93% | 2.75 | 2.94 |
| settlements :: PATCH /api/v1/settlements/{settlement_id}/status | PATCH | /settlements/1/status | 10.94 | 11.31 | -0.37 | -3.36% | 20.88 | 13.25 |
| admin :: GET /api/v1/admin/rides/{ride_id}/chats | GET | /admin/rides/20026/chats | 7.57 | 7.83 | -0.27 | -3.53% | 8.90 | 8.36 |
| bookings :: POST /api/v1/rides/bookings/{booking_id}/accept | POST | /rides/bookings/30061/accept | 16.81 | 17.41 | -0.60 | -3.58% | 25.60 | 36.32 |
| admin :: GET /api/v1/admin/members | GET | /admin/members | 2642.95 | 2770.09 | -127.14 | -4.81% | 2820.27 | 2890.06 |
| settlements :: GET /api/v1/settlements/my | GET | /settlements/my | 25.07 | 26.29 | -1.21 | -4.84% | 26.27 | 29.08 |
| admin :: GET /api/v1/admin/tables/{table_name} | GET | /admin/tables/Locations | 10.29 | 10.87 | -0.58 | -5.62% | 11.25 | 12.54 |
| admin :: DELETE /api/v1/admin/tables/{table_name}/{pk} | DELETE | /admin/tables/Locations/1051 | 13.17 | 13.98 | -0.81 | -6.12% | 14.55 | 32.19 |
| bookings :: DELETE /api/v1/rides/bookings/{booking_id} | DELETE | /rides/bookings/30061 | 11.73 | 12.47 | -0.73 | -6.24% | 12.54 | 16.63 |
| admin :: POST /api/v1/admin/tables/{table_name} | POST | /admin/tables/Locations | 12.66 | 13.46 | -0.80 | -6.28% | 18.44 | 28.79 |
| rides :: PATCH /api/v1/rides/{ride_id} | PATCH | /rides/20026 | 9.14 | 9.81 | -0.67 | -7.30% | 12.56 | 12.52 |
| reviews :: GET /api/v1/reviews/my | GET | /reviews/my | 7.93 | 8.58 | -0.65 | -8.24% | 9.75 | 9.90 |
| reviews :: DELETE /api/v1/reviews/{review_id} | DELETE | /reviews/15059 | 10.88 | 11.78 | -0.90 | -8.27% | 11.99 | 22.49 |
| saved-addresses :: DELETE /api/v1/saved-addresses/{address_id} | DELETE | /saved-addresses/26 | 9.61 | 10.79 | -1.19 | -12.36% | 11.56 | 19.62 |
| settlements :: GET /api/v1/settlements/booking/{booking_id} | GET | /settlements/booking/30061 | 7.49 | 9.04 | -1.55 | -20.65% | 8.47 | 13.44 |
| preferences :: PUT /api/v1/preferences/me | PUT | /preferences/me | 10.96 | 13.80 | -2.85 | -26.01% | 12.13 | 26.39 |
| admin :: GET /api/v1/admin/rides/{ride_id}/participants | GET | /admin/rides/20026/participants | 7.44 | 9.68 | -2.24 | -30.16% | 8.44 | 14.80 |
| reviews :: GET /api/v1/reviews/member/{member_id} | GET | /reviews/member/20027 | 8.37 | 10.99 | -2.62 | -31.23% | 9.05 | 25.54 |
| auth :: GET /api/v1/auth/me | GET | /auth/me | 5.59 | 7.92 | -2.33 | -41.73% | 6.52 | 12.06 |
