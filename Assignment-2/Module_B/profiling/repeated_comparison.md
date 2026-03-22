# Repeated Benchmark Comparison (Before vs After Indexing)

- Repetitions per mode: 5
- Endpoints compared: 50
- Improved: 30
- Regressed: 20
- Unchanged: 0

## Top 20 Improvements (mean avg latency)

| Endpoint | Before mean±std (ms) | After mean±std (ms) | Delta (ms) | Improve % | Before success % | After success % |
|---|---:|---:|---:|---:|---:|---:|
| admin :: GET /api/v1/admin/rides/active | 18.59±0.21 | 5.54±0.16 | 13.04 | 70.18% | 100.0% | 100.0% |
| rides :: GET /api/v1/rides | 21.86±1.68 | 14.43±8.72 | 7.43 | 33.99% | 100.0% | 100.0% |
| admin :: GET /api/v1/admin/rides/stats | 92.58±1.87 | 71.95±0.36 | 20.63 | 22.28% | 100.0% | 100.0% |
| locations :: GET /api/v1/locations/{location_id} | 5.02±1.06 | 4.50±0.35 | 0.52 | 10.33% | 100.0% | 100.0% |
| admin :: GET /api/v1/admin/tables | 7.21±0.89 | 6.47±0.05 | 0.74 | 10.23% | 100.0% | 100.0% |
| admin :: GET /api/v1/admin/rides/{ride_id}/participants | 7.99±1.05 | 7.29±0.07 | 0.70 | 8.77% | 100.0% | 100.0% |
| settlements :: GET /api/v1/settlements/booking/{booking_id} | 7.99±1.23 | 7.31±0.25 | 0.68 | 8.48% | 100.0% | 100.0% |
| admin :: PATCH /api/v1/admin/tables/{table_name}/{pk} | 14.59±2.81 | 13.74±1.12 | 0.86 | 5.87% | 100.0% | 100.0% |
| rides :: DELETE /api/v1/rides/{ride_id} | 10.42±0.41 | 9.85±0.22 | 0.57 | 5.50% | 100.0% | 100.0% |
| chat :: GET /api/v1/chat/ride/{ride_id} | 7.68±0.98 | 7.26±0.12 | 0.42 | 5.41% | 100.0% | 100.0% |
| locations :: GET /api/v1/locations | 7.62±0.30 | 7.27±0.19 | 0.35 | 4.55% | 100.0% | 100.0% |
| bookings :: DELETE /api/v1/rides/bookings/{booking_id} | 12.06±0.50 | 11.67±0.43 | 0.39 | 3.22% | 100.0% | 100.0% |
| rides :: GET /api/v1/rides/{ride_id}/with-bookings | 8.36±0.94 | 8.09±0.59 | 0.27 | 3.18% | 100.0% | 100.0% |
| admin :: GET /api/v1/admin/rides/{ride_id}/chats | 7.36±0.16 | 7.14±0.24 | 0.23 | 3.09% | 100.0% | 100.0% |
| rides :: POST /api/v1/rides/{ride_id}/end | 7.59±0.35 | 7.36±0.29 | 0.23 | 2.98% | 0.0% | 0.0% |
| saved-addresses :: PATCH /api/v1/saved-addresses/{address_id} | 10.99±0.43 | 10.69±0.34 | 0.30 | 2.72% | 100.0% | 100.0% |
| admin :: PATCH /api/v1/admin/members/{member_id}/role | 8.68±0.12 | 8.45±0.22 | 0.23 | 2.70% | 100.0% | 100.0% |
| testing :: GET /api/v1/health | 2.16±0.08 | 2.12±0.15 | 0.05 | 2.17% | 100.0% | 100.0% |
| reviews :: POST /api/v1/reviews | 14.09±0.39 | 13.80±0.31 | 0.29 | 2.08% | 100.0% | 100.0% |
| bookings :: POST /api/v1/rides/bookings/{booking_id}/reject | 12.73±0.41 | 12.50±0.42 | 0.23 | 1.78% | 100.0% | 100.0% |

## Full Comparison

| Endpoint | Method | URL | Before mean | After mean | Delta | Improve % |
|---|---|---|---:|---:|---:|---:|
| admin :: GET /api/v1/admin/rides/active | GET | /admin/rides/active | 18.59 | 5.54 | 13.04 | 70.18% |
| rides :: GET /api/v1/rides | GET | /rides | 21.86 | 14.43 | 7.43 | 33.99% |
| admin :: GET /api/v1/admin/rides/stats | GET | /admin/rides/stats | 92.58 | 71.95 | 20.63 | 22.28% |
| locations :: GET /api/v1/locations/{location_id} | GET | /locations/1031 | 5.02 | 4.50 | 0.52 | 10.33% |
| admin :: GET /api/v1/admin/tables | GET | /admin/tables | 7.21 | 6.47 | 0.74 | 10.23% |
| admin :: GET /api/v1/admin/rides/{ride_id}/participants | GET | /admin/rides/20026/participants | 7.99 | 7.29 | 0.70 | 8.77% |
| settlements :: GET /api/v1/settlements/booking/{booking_id} | GET | /settlements/booking/30061 | 7.99 | 7.31 | 0.68 | 8.48% |
| admin :: PATCH /api/v1/admin/tables/{table_name}/{pk} | PATCH | /admin/tables/Locations/1051 | 14.59 | 13.74 | 0.86 | 5.87% |
| rides :: DELETE /api/v1/rides/{ride_id} | DELETE | /rides/20026 | 10.42 | 9.85 | 0.57 | 5.50% |
| chat :: GET /api/v1/chat/ride/{ride_id} | GET | /chat/ride/20026 | 7.68 | 7.26 | 0.42 | 5.41% |
| locations :: GET /api/v1/locations | GET | /locations | 7.62 | 7.27 | 0.35 | 4.55% |
| bookings :: DELETE /api/v1/rides/bookings/{booking_id} | DELETE | /rides/bookings/30061 | 12.06 | 11.67 | 0.39 | 3.22% |
| rides :: GET /api/v1/rides/{ride_id}/with-bookings | GET | /rides/20027/with-bookings | 8.36 | 8.09 | 0.27 | 3.18% |
| admin :: GET /api/v1/admin/rides/{ride_id}/chats | GET | /admin/rides/20026/chats | 7.36 | 7.14 | 0.23 | 3.09% |
| rides :: POST /api/v1/rides/{ride_id}/end | POST | /rides/20026/end | 7.59 | 7.36 | 0.23 | 2.98% |
| saved-addresses :: PATCH /api/v1/saved-addresses/{address_id} | PATCH | /saved-addresses/26 | 10.99 | 10.69 | 0.30 | 2.72% |
| admin :: PATCH /api/v1/admin/members/{member_id}/role | PATCH | /admin/members/20028/role | 8.68 | 8.45 | 0.23 | 2.70% |
| testing :: GET /api/v1/health | GET | /health | 2.16 | 2.12 | 0.05 | 2.17% |
| reviews :: POST /api/v1/reviews | POST | /reviews | 14.09 | 13.80 | 0.29 | 2.08% |
| bookings :: POST /api/v1/rides/bookings/{booking_id}/reject | POST | /rides/bookings/30061/reject | 12.73 | 12.50 | 0.23 | 1.78% |
| admin :: DELETE /api/v1/admin/tables/{table_name}/{pk} | DELETE | /admin/tables/Locations/1051 | 14.57 | 14.33 | 0.25 | 1.68% |
| admin :: POST /api/v1/admin/tables/{table_name} | POST | /admin/tables/Locations | 13.85 | 13.63 | 0.23 | 1.65% |
| reviews :: DELETE /api/v1/reviews/{review_id} | DELETE | /reviews/15059 | 11.20 | 11.05 | 0.15 | 1.37% |
| settlements :: PATCH /api/v1/settlements/{settlement_id}/status | PATCH | /settlements/1/status | 11.12 | 10.97 | 0.15 | 1.35% |
| bookings :: POST /api/v1/rides/{ride_id}/book | POST | /rides/20026/book | 12.22 | 12.07 | 0.16 | 1.27% |
| saved-addresses :: DELETE /api/v1/saved-addresses/{address_id} | DELETE | /saved-addresses/26 | 9.77 | 9.65 | 0.12 | 1.23% |
| rides :: POST /api/v1/rides/{ride_id}/start | POST | /rides/20026/start | 15.94 | 15.78 | 0.16 | 1.02% |
| auth :: POST /api/v1/auth/login | POST | /auth/login | 251.47 | 249.33 | 2.13 | 0.85% |
| auth :: POST /api/v1/auth/register | POST | /auth/register | 267.31 | 266.73 | 0.58 | 0.22% |
| reviews :: GET /api/v1/reviews/ride/{ride_id} | GET | /reviews/ride/20029 | 7.04 | 7.03 | 0.01 | 0.19% |
| testing :: GET /api/v1/testing/db | GET | /testing/db | 3.99 | 4.01 | -0.02 | -0.55% |
| admin :: GET /api/v1/admin/audit-logs | GET | /admin/audit-logs | 32.07 | 32.32 | -0.25 | -0.76% |
| rides :: PATCH /api/v1/rides/{ride_id} | PATCH | /rides/20026 | 9.65 | 9.76 | -0.11 | -1.13% |
| admin :: GET /api/v1/admin/rides/completed | GET | /admin/rides/completed | 216.02 | 218.93 | -2.90 | -1.34% |
| bookings :: POST /api/v1/rides/bookings/{booking_id}/accept | POST | /rides/bookings/30061/accept | 16.36 | 16.71 | -0.35 | -2.15% |
| saved-addresses :: POST /api/v1/saved-addresses | POST | /saved-addresses | 10.71 | 10.96 | -0.25 | -2.33% |
| admin :: GET /api/v1/admin/rides/open | GET | /admin/rides/open | 222.32 | 227.89 | -5.58 | -2.51% |
| rides :: POST /api/v1/rides | POST | /rides | 17.38 | 17.88 | -0.51 | -2.91% |
| bookings :: GET /api/v1/rides/{ride_id}/bookings/pending | GET | /rides/20026/bookings/pending | 7.96 | 8.20 | -0.24 | -2.98% |
| admin :: GET /api/v1/admin/members | GET | /admin/members | 2664.62 | 2744.92 | -80.30 | -3.01% |
| admin :: GET /api/v1/admin/tables/{table_name} | GET | /admin/tables/Locations | 10.51 | 10.83 | -0.33 | -3.10% |
| settlements :: GET /api/v1/settlements/my | GET | /settlements/my | 24.89 | 25.93 | -1.04 | -4.18% |
| auth :: GET /api/v1/auth/me | GET | /auth/me | 5.44 | 5.70 | -0.25 | -4.64% |
| preferences :: PUT /api/v1/preferences/me | PUT | /preferences/me | 11.34 | 12.14 | -0.80 | -7.09% |
| preferences :: GET /api/v1/preferences/me | GET | /preferences/me | 6.73 | 7.24 | -0.51 | -7.53% |
| saved-addresses :: GET /api/v1/saved-addresses | GET | /saved-addresses | 5.88 | 6.33 | -0.45 | -7.67% |
| locations :: POST /api/v1/locations | POST | /locations | 7.71 | 8.38 | -0.66 | -8.59% |
| reviews :: GET /api/v1/reviews/my | GET | /reviews/my | 8.15 | 8.95 | -0.80 | -9.79% |
| bookings :: GET /api/v1/rides/my/bookings | GET | /rides/my/bookings | 7.66 | 8.92 | -1.26 | -16.43% |
| reviews :: GET /api/v1/reviews/member/{member_id} | GET | /reviews/member/20027 | 8.78 | 10.49 | -1.71 | -19.53% |
